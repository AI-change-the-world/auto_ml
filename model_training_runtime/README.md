# Model Training Runtime (Experimental)

`model_training_runtime` executes versioned user training-code packages on a
dedicated worker. It coexists with `model_trainer`: built-in training is
unchanged, while user-uploaded scripts take the runtime path.

The runtime keeps the FastAPI service, runner, bounded subprocess, OpenDAL
input materialization, and framework dependencies in one image. Compose runs a
separate worker container that consumes only the dedicated custom-training
queue; it never consumes the legacy trainer queue.

## Current Scope

The HTTP API and worker provide validation, immutable registration, ZIP
configuration inspection, and explicitly enabled execution:

- validates `training_package.json` against `training-code-package/v1`
- validates dataset manifests, execution requests, JSONL events, final results, and the MQ submission payload
- validates training-code ZIPs and model-package ZIPs: root manifests, referenced members, path traversal, duplicate members, symlinks, and archive size limits
- provides read-only ZIP configuration inspection for a future package-management UI; inspection returns only a validated manifest and archive metadata, never source code or model/checkpoint bytes
- can register validated code releases, model packages, and dataset source snapshots as immutable objects through the platform's existing OpenDAL S3 configuration
- consumes immutable `training-code-submit/v1` messages from `training.code.execute` when Nacos enables `model-training-runtime.execution.enabled`
- persists verified output artifacts before deleting the workspace
- returns task status/log updates and registers only compatible deployable ONNX outputs

The service contains the runtime foundation, runner, execution coordinator,
and code-package templates. The coordinator materializes immutable dataset and
model inputs, creates a task workspace, launches the package in a bounded
subprocess, parses runner protocol output, and verifies the terminal result.
The direct endpoint and the worker clean each workspace after verified artifacts
are persisted. The worker uses existing task lifecycle messages, and only
deployable ONNX artifacts matching existing inference templates are registered.

It must not be pointed at the existing `trainer.task.queue`. Production use
requires platform-managed package approval, container/job isolation, and an
egress policy appropriate for submitted code.

## Replacement Plan

`model_trainer` remains the production owner of the current training queue, task lifecycle, and Ultralytics jobs. This service can only replace it incrementally after each gate is passed:

1. contract stability: a platform-owned sample package and an external-framework package validate and have approved versioned examples
2. direct execution: the in-service coordinator, bounded subprocess, cancellation, logs, events, and GPU resource policy are verified
3. artifact handling: verified artifacts are stored and compatible deployable ONNX is registered
4. shadow mode: the same non-production jobs run through both paths and outputs/events are compared
5. cutover: `automl_server` explicitly submits selected tasks to a dedicated routing key; only then can a task type move away from `model_trainer`

The old and new workers must never consume the same training task queue. Cutover is controlled at the producer, task type, or explicitly selected training backend.

## Security Position

Static package validation is a correctness check, not a security boundary. The
direct execution phase accepts platform-approved packages only. It uses a
task-local workspace, a bounded subprocess, and service-owned Python
dependencies; ZIP packages cannot install dependencies or choose an executable.
Arbitrary user code still needs stronger filesystem/network isolation in a
multi-tenant deployment. `script_managed` data is disabled until Nacos sets
`allow_script_managed_data: true`; that application switch is not a network
boundary, so production deployments must also enforce an egress allowlist.

Dependencies are selected through `runtime.id`, which names an allowlisted
Python environment already installed in this service. Ultralytics is currently
the first such environment. A package does not get to install arbitrary
dependencies through `requirements.txt`.

## Runtime Foundation

The Sandbox runtime modules are carried into `model_training_runtime/runtime/`
with training-specific names and policy:

| Module | Future responsibility | Current status |
| --- | --- | --- |
| `archive.py` | Safe package ZIP inspection and extraction | Used by ZIP validation; rejects `.env` and dynamic dependency files. |
| `config.py`, `models.py` | Shared runtime values and execution limits | Defined and test-covered. |
| `environment.py` | Resolves an allowlisted Python executable and prepares task-local environment paths | Used by the direct in-service execution path; never accepts package executables or runs package pip commands. |
| `errors.py`, `logging_utils.py` | Structured operational diagnostics | Defined and used by runtime modules. |
| `process.py`, `limits.py` | Output-bounded process tree control and optional Linux `prlimit` defense-in-depth limits | Defined and test-covered; no app path calls it. |
| `protocol.py`, `parsing.py` | Parses prefixed runner event/log/result lines | Defined and test-covered. |
| `executor.py` | Execution-backend contract and service subprocess implementation | `ServiceSubprocessExecutor` is used by the direct endpoint; the old local executor remains a test helper. |
| `coordinator.py` | Materializes pinned inputs, builds a private workspace, invokes the runner, and verifies the terminal outcome | Used by the direct endpoint and dedicated worker. |

The deliberate difference from `ai_pipeline_sandbox/runtime/environment.py` is
that training packages cannot provide `.env`, `requirements.txt`, local wheels,
or other arbitrary dependency installation. The service image owns framework
dependencies and the runtime registry only selects an allowlisted environment.

An isolated container or Job executor may become useful for arbitrary user code
or stricter GPU/network isolation. It is intentionally a future direction, not
part of this validation phase.

## Contracts

All contracts are versioned and reject unknown fields. Version 1 defines:

| Contract | Version | Direction | Purpose |
| --- | --- | --- | --- |
| Package manifest | `training-code-package/v1` | ZIP -> runtime | Declares code entrypoint, supported tasks, platform runtime, parameter schema, and expected artifacts. |
| Dataset source manifest | `training-dataset-source-manifest/v1` | platform task resolver -> registry | Pins the existing dataset and annotation S3 object paths before workers run. |
| Dataset manifest | `training-dataset-manifest/v1` | materializer -> package | Lists local files materialized from that immutable S3 source snapshot. Package code must not call the platform API to rediscover data. |
| Model package manifest | `training-model-package/v1` | model ZIP -> registry | Declares the initialization artifact plus an optional fully resumable checkpoint, framework identity, task kind, class order, and format. |
| Execution request | `training-execution/v1` | runtime -> package | Carries task, resolved package digest, workspace paths, parameters, resources, and optional materialized model input. |
| Event | `training-event/v1` | package -> runtime | JSONL progress: phase, log, metric, or checkpoint. `sequence` is monotonic per execution. |
| Result | `training-result/v1` | package -> runtime | `result.json` states terminal outcome, metrics, artifacts, model metadata, and errors. |
| MQ submission | `training-code-submit/v1` | control plane -> runtime worker | Immutable MQ payload that refers to package and dataset objects by key and SHA-256. |

The coordinator invokes the package function `train(context, report)` through
the in-service subprocess executor. A future container executor can invoke the
same function with the workspace mounted at `/workspace`. The `report`
callback emits a validated event. Package artifacts must be created below the
runtime-owned output directory. The runner, rather than package code,
calculates artifact size and SHA-256, writes `result.json`, and emits the
terminal result.

The runner's stdout protocol mirrors the Sandbox pattern and is consumed by the
dedicated worker:

```text
__AUTO_ML_TRAINING_EVENT__={...}
__AUTO_ML_TRAINING_LOG__={...}
__AUTO_ML_TRAINING_RESULT__={...}
```

Package code supplies only event-specific fields to `report`; it must not set
`protocol_version`, `execution_id`, `sequence`, or `occurred_at`.

### Admission Rules

Structural validation says that one JSON document is well-formed. Admission
validation says that a particular package is allowed to run a particular task,
and that its result fulfills the package declaration. Both validations happen
before this service has any MQ or execution wiring.

- `parameters_schema` must be a valid Draft 2020-12 JSON Schema with object root; execution parameters must satisfy it.
- Package key/version and `runtime` must match the resolved execution request.
- The package must declare the execution task kind, data modalities, and annotation kinds.
- `code_dir`, `input_dir`, and `output_dir` must be distinct children of the workspace; the dataset manifest and optional materialized model input live beneath `input_dir`.
- The platform resolves the current task's database records into dataset/annotation S3 references, pins their content digest and size with OpenDAL, and stores the immutable source snapshot before execution. User packages never see database IDs, S3 credentials, or arbitrary URLs.
- A model input must match the package's declared framework, supported format, and task kind. `resume` is accepted only for a model-package checkpoint explicitly marked resumable; a generic `.pt`/`.ckpt` weight is initialization-only.
- Every successful result artifact must match exactly one declared role/deployable pair and an allowed format; all declared required artifacts must be present.
- If required by the package, model metadata is mandatory and must carry exactly the task kind and class names from the dataset manifest.

`POST /v1/admission/execution/validate` accepts `{ "manifest", "execution" }`.
`POST /v1/admission/result/validate` additionally accepts `result`. The runner
applies result admission itself whenever the worker includes the
resolved `package_manifest` in its private execution context. This optional
field is runtime-internal; external producers should submit only a package
reference and digest.

### Package ZIP

```text
my-training-package.zip
├── training_package.json    # Required at ZIP root
├── train.py                 # Required entrypoint from the manifest
└── src/                     # Optional package modules and static assets
```

The included [template](./templates/training-package/README.md) provides a
runnable boilerplate package. The
[PyTorch cat/dog example](./examples/pytorch-image-classifier/README.md) is a
real script-managed example: it downloads CIFAR-10, trains a small classifier,
and exports deployable ONNX. The
[Ultralytics detection example](./examples/ultralytics-detection/README.md)
adapts a materialized platform dataset, trains a selected `.pt` model, emits
metrics, and produces model/checkpoint artifacts. Both examples include a
deterministic ZIP builder.

Ultralytics belongs to the platform service image, not to a submitted package.
Its pinned dependencies are in [requirements.txt](./requirements.txt), and the
runtime id is `ultralytics-8.3.0-pytorch-2.5-cu124`.

### Dataset and Model Inputs

For `platform_dataset`, the control plane resolves datasets from the current platform
models exactly as `model_trainer` does today: assets come from the datasets
bucket and annotation records from the annotations bucket. It submits a
`training-dataset-source-manifest/v1` to
`POST /v1/registrations/dataset-snapshots`; registration reads each object
through OpenDAL, records its SHA-256 and size, and stores an immutable source
manifest in the default bucket. The worker later reads only that snapshot and
materializes files under its task-local `input_dir`.

The control plane currently exposes the prerequisite read-only preview at
`POST /task/training-dataset-snapshot/preview`. It builds the source manifest
from the same task source selection as the legacy trainer, but does not create
a task, read object bodies, call this runtime, write S3, or publish MQ. Calling
the runtime registration endpoint is an explicit second step through
`POST /task/training-dataset-snapshot/register`, and remains disabled unless
the shared Nacos `AUTO_ML_CONFIG.model-training-runtime.enabled` is true and
its `base_url` is configured. It pins the current object content through
OpenDAL but still does not create a task, publish MQ, or execute code. Repeated
registrations of the same resolved content return the same immutable snapshot
with `created: false`. When the same Nacos block configures `token`, all
registry write endpoints require its `Authorization: Bearer ...` value.

For custom-script model inputs and incremental training, upload a ZIP following the
[model-package template](./templates/model-package/README.md). The registry
stores the original ZIP and each declared selected artifact in the existing
models bucket. A normal weight is returned as an `initialize` input. A ZIP may
also declare a distinct `resume_checkpoint_path`; only that returned artifact
is eligible for `resume`. This avoids confusing inference weights with an
optimizer/scheduler-bearing training checkpoint and keeps framework/version,
task kind, and class order checks explicit.

Model-package imports currently use an in-memory HTTP body and are deliberately
capped at 512 MiB compressed and uncompressed. Larger imports need the next
phase's scoped direct-to-S3 upload flow rather than an unbounded API request.

The control plane registers code packages and model packages in its separate
runtime catalogs through `/training-runtime/code-packages/import` and
`/training-runtime/model-packages/import`. Those catalogs are not `base_models`:
they must only be selected by a future custom-script training task, never by
`model_trainer`.

Every declared output is stored below
`training-code-runtime/executions/<execution_id>/...`. Checkpoints remain
training artifacts. Only a declared deployable ONNX model compatible with an
existing detection or classification inference template enters `AvailableModel`.

`script_managed` is for packages that own their data acquisition or generation.
The submission deliberately has no dataset/annotation IDs and scripts receive
an empty dataset item list plus declared modalities and class order. The mode
is rejected unless Nacos enables `allow_script_managed_data: true`. That switch
is not a network boundary: packages that download data need a container- or
network-level egress allowlist, and packages that do not need network access
should run with egress disabled.

## Direct Execution API

`POST /v1/executions/run` accepts a validated `training-code-submit/v1` payload
whose package and dataset references point to immutable OpenDAL/S3 objects. It
is disabled unless Nacos contains:

```yaml
model-training-runtime:
  execution:
    enabled: true
    runtime_ids:
      - ultralytics-8.3.0-pytorch-2.5-cu124
    # Optional platform-owned settings:
    # python_executable: /opt/conda/bin/python
    # workspace_root: /app/runtime-data/workspaces
    # idle_timeout_seconds: 180
```

The endpoint performs package digest verification, dataset/model materializing,
admission checks, runner execution, event/result validation, artifact
persistence, and workspace cleanup in one request. It returns result metadata,
events, logs, and immutable artifact references. Normal training should use
the asynchronous worker rather than this diagnostic endpoint.

## MQ Worker

The worker uses dedicated infrastructure rather than the legacy trainer queue:

| Purpose | Queue | Routing key | Contract |
| --- | --- | --- | --- |
| Submit code-training execution | `training.code.execute` | `training.code.execute` | `training-code-submit/v1` |
| Runtime task lifecycle | existing `task.log` / `task.status.update` | existing keys | platform task lifecycle |
| Deployable ONNX registration | existing `model.registered` | existing key | platform model lifecycle |

The control plane stores each immutable submission in `training_runtime_execution`.
Task and execution IDs are unique; the worker uses `prefetch=1`, updates queued,
running, succeeded, and failed states through the normal task-status messages,
and includes the execution ID for deduplication.

## HTTP Validation API

`/inspect` is the UI-oriented, read-only counterpart to `/validate`. It uses
the same safe archive validation, but returns a stable envelope containing the
validated root manifest as `configuration` and archive digest/size metadata as
`archive`. It does not import package Python, deserialize model files, or
return ZIP member contents. Registration, execution, task creation, and MQ
publication are all out of scope for inspection.

```json
{
  "kind": "training_code_package",
  "valid": true,
  "archive": {
    "sha256": "...",
    "file_count": 2,
    "uncompressed_bytes": 1234
  },
  "configuration": {
    "protocol_version": "training-code-package/v1"
  }
}
```

| Method | Endpoint | Contract |
| --- | --- | --- |
| `GET` | `/health` | Reports whether Nacos enabled the in-service execution path. |
| `GET` | `/v1/contracts` | Lists supported contract versions. |
| `POST` | `/v1/contracts/package/validate` | Package manifest JSON. |
| `POST` | `/v1/packages/archive/validate` | ZIP body with `Content-Type: application/zip`; validates only, never executes code. |
| `POST` | `/v1/packages/archive/inspect` | Read-only training-code ZIP inspection; returns validated `training_package.json` as `configuration`, plus archive metadata. |
| `POST` | `/v1/model-packages/archive/validate` | Model ZIP body; validates manifest and selected artifact members without deserializing model bytes. |
| `POST` | `/v1/model-packages/archive/inspect` | Read-only model ZIP inspection; returns validated `training_model_package.json` as `configuration`, plus archive metadata. |
| `POST` | `/v1/contracts/dataset-manifest/validate` | Dataset manifest JSON. |
| `POST` | `/v1/contracts/dataset-source-manifest/validate` | Existing platform S3 source manifest JSON. |
| `POST` | `/v1/contracts/execution/validate` | Execution request JSON. |
| `POST` | `/v1/admission/execution/validate` | Cross-validates package manifest and execution request. |
| `POST` | `/v1/contracts/event/validate` | One event JSON. |
| `POST` | `/v1/contracts/result/validate` | Final result JSON. |
| `POST` | `/v1/admission/result/validate` | Cross-validates manifest, execution request, and terminal result. |
| `POST` | `/v1/contracts/mq-submission/validate` | Reserved MQ submission JSON. |
| `POST` | `/v1/executions/run` | Experimental direct execution of one registered submission inside this service. |
| `POST` | `/v1/registrations/packages` | Stores a validated training-code ZIP as an immutable default-bucket release. |
| `POST` | `/v1/registrations/model-packages` | Imports a validated base-model ZIP into immutable models-bucket artifacts. |
| `POST` | `/v1/registrations/dataset-snapshots` | Pins and stores a resolved S3 dataset source manifest through OpenDAL. |

Run locally:

```bash
cd model_training_runtime
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8012
python -m unittest discover -s tests -v
```

The direct execution endpoint and MQ worker both invoke `runner.py` as a bounded
subprocess. Compose includes the `model-training-runtime` API service and the
separate `model-training-runtime-worker`; both are inert until the Nacos block
below is explicitly enabled.

## Enabling Execution

Set this Nacos configuration only after the runtime image, required framework
dependencies, storage access, and isolation policy are ready:

```yaml
model-training-runtime:
  enabled: true
  base_url: http://model-training-runtime:8012
  allow_script_managed_data: false
  execution:
    enabled: true
    runtime_ids:
      - ultralytics-8.3.0-pytorch-2.5-cu124
      - pytorch-2.5-cu124
```

Keep `allow_script_managed_data` false for normal platform-dataset training. To
run the CIFAR-10 cat/dog example, enable it only together with an explicit
egress policy that permits the required download host.



## Development
```
uvicorn app:app --host 0.0.0.0 --port 8012
```