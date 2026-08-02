# Training Code Runtime (Experimental)

`training_code_runtime` is an exploratory service for running versioned user training-code packages on platform-managed training runtimes. It is deliberately **not** a replacement for `model_trainer` yet.

The purpose of this first implementation is to freeze and exercise the boundaries before taking on the difficult parts of training execution: package metadata, materialized dataset input, resource allocation, training events, artifacts, result registration, and future MQ submission messages.

## Current Scope

This service currently provides only non-executing validation:

- validates `training_package.json` against `training-code-package/v1`
- validates dataset manifests, execution requests, JSONL events, final results, and the future MQ submission payload
- validates an uploaded ZIP layout, root manifest, entrypoint presence, path traversal, duplicate members, symlinks, and archive size limits
- never imports the submitted Python code, installs its dependencies, reads object storage, starts a subprocess, or consumes a RabbitMQ queue

The repository also contains a **dormant runtime foundation**, runner, and
code-package template. The runtime foundation has the Sandbox-derived modules
needed by a later worker: safe ZIP extraction, structured errors, process
control, line parsing, optional inner process limits, workspace preparation,
and platform runtime resolution. They are only exercised by local tests at this
point. The HTTP API cannot invoke the runner, and the runtime does not download
packages, install dependencies, or connect to MQ.

It must not be used for production training or be pointed at the existing `trainer.task.queue`.

## Replacement Plan

`model_trainer` remains the production owner of the current training queue, task lifecycle, and Ultralytics jobs. This service can only replace it incrementally after each gate is passed:

1. contract stability: a platform-owned sample package and an external-framework package validate and have approved versioned examples
2. controlled execution: per-task isolated workspace, platform-managed runtime image, bounded process, cancellation, logs, and events are implemented
3. artifact handling: artifact checks, temporary upload credentials, model registration, and deployment compatibility checks are implemented
4. shadow mode: the same non-production jobs run through both paths and outputs/events are compared
5. cutover: `automl_server` explicitly submits selected tasks to the new dedicated routing key; only then can a task type move away from `model_trainer`

The old and new workers must never consume the same training task queue. Cutover is controlled at the producer, task type, or explicitly selected training backend.

## Security Position

Static package validation is a correctness check, not a security boundary. Submitted Python is untrusted once execution exists. Execution therefore requires a per-task container or Job with a read-only input mount, write-only output directory, short-lived scoped storage credentials, GPU/CPU/memory/time/process quotas, and an explicit network policy. The first execution phase accepts platform-approved code packages only; arbitrary user code is a later product and security decision.

Dependencies are selected through `runtime.id`, which names a platform-managed immutable image such as `pytorch-2.5-cu124`. A package does not get to install arbitrary dependencies through `requirements.txt`.

## Runtime Foundation

The Sandbox runtime modules are carried into `training_code_runtime/runtime/`
with training-specific names and policy:

| Module | Future responsibility | Current status |
| --- | --- | --- |
| `archive.py` | Safe package ZIP inspection and extraction | Used by ZIP validation; rejects `.env` and dynamic dependency files. |
| `config.py`, `models.py` | Shared runtime values and execution limits | Defined and test-covered. |
| `environment.py` | Resolves an allowlisted, digest-pinned platform runtime and prepares task-local environment paths | Defined and test-covered; never creates venvs or runs pip. |
| `errors.py`, `logging_utils.py` | Structured operational diagnostics | Defined and used by runtime modules. |
| `process.py`, `limits.py` | Output-bounded process tree control and optional Linux `prlimit` defense-in-depth limits | Defined and test-covered; no app path calls it. |
| `protocol.py`, `parsing.py` | Parses prefixed runner event/log/result lines | Defined and test-covered. |

The deliberate difference from `ai_pipeline_sandbox/runtime/environment.py` is
that training packages cannot provide `.env`, `requirements.txt`, local wheels,
or other arbitrary dependency installation. Those risks are replaced with a
platform-maintained runtime registry and immutable image digest.

## Contracts

All contracts are versioned and reject unknown fields. Version 1 defines:

| Contract | Version | Direction | Purpose |
| --- | --- | --- | --- |
| Package manifest | `training-code-package/v1` | ZIP -> runtime | Declares code entrypoint, supported tasks, platform runtime, parameter schema, and expected artifacts. |
| Dataset manifest | `training-dataset-manifest/v1` | orchestrator -> package | Lists the local, materialized data and annotation files. Package code must not call the platform API to rediscover data. |
| Execution request | `training-execution/v1` | runtime -> package | Carries task, resolved package digest, workspace paths, parameters, resources, and optional resume input. |
| Event | `training-event/v1` | package -> runtime | JSONL progress: phase, log, metric, or checkpoint. `sequence` is monotonic per execution. |
| Result | `training-result/v1` | package -> runtime | `result.json` states terminal outcome, metrics, artifacts, model metadata, and errors. |
| MQ submission | `training-code-submit/v1` | future producer -> runtime | Immutable MQ payload that refers to package and dataset objects by key and SHA-256. |

The first execution adapter will invoke the package function `train(context, report)`. `context` is the `TrainingExecutionRequest` JSON; it only contains paths below `/workspace`. The `report` callback emits a validated event. Package artifacts must be created below the runtime-owned output directory. The runner, rather than package code, calculates artifact size and SHA-256, writes `result.json`, and emits the terminal result.

The dormant runner's stdout protocol mirrors the Sandbox pattern and is for the
future worker only:

```text
__AUTO_ML_TRAINING_EVENT__={...}
__AUTO_ML_TRAINING_LOG__={...}
__AUTO_ML_TRAINING_RESULT__={...}
```

Package code supplies only event-specific fields to `report`; it must not set
`protocol_version`, `execution_id`, `sequence`, or `occurred_at`.

### Package ZIP

```text
my-training-package.zip
├── training_package.json    # Required at ZIP root
├── train.py                 # Required entrypoint from the manifest
└── src/                     # Optional package modules and static assets
```

The included [template](./templates/training-package/README.md) provides a runnable boilerplate package with a placeholder export. The [example](./examples/pytorch-image-classifier/training_package.json) remains a minimal manifest-only declaration.

## MQ Reservation

No MQ queue is declared or consumed by this service today. The contract is prepared now so the later worker wiring does not require a message redesign.

When controlled execution is approved, use dedicated infrastructure rather than the legacy trainer queue:

| Purpose | Queue | Routing key | Contract |
| --- | --- | --- | --- |
| Submit code-training execution | `training.code.execute` | `training.code.execute` | `training-code-submit/v1` |
| Runtime event | `training.code.event` | `training.code.event` | `training-event/v1` |
| Terminal runtime result | `training.code.result` | `training.code.result` | `training-result/v1` |

The eventual worker will acknowledge the submission only after persisting/claiming an idempotent `execution_id`. `message_id` identifies a delivery attempt; `execution_id` identifies the logical run. Event and result consumers must deduplicate on those identifiers.

## HTTP Validation API

| Method | Endpoint | Contract |
| --- | --- | --- |
| `GET` | `/health` | Shows `contract_validation_only`; `execution_enabled` and `mq_consumer_enabled` are both false. |
| `GET` | `/v1/contracts` | Lists supported contract versions. |
| `POST` | `/v1/contracts/package/validate` | Package manifest JSON. |
| `POST` | `/v1/packages/archive/validate` | ZIP body with `Content-Type: application/zip`; validates only, never executes code. |
| `POST` | `/v1/contracts/dataset-manifest/validate` | Dataset manifest JSON. |
| `POST` | `/v1/contracts/execution/validate` | Execution request JSON. |
| `POST` | `/v1/contracts/event/validate` | One event JSON. |
| `POST` | `/v1/contracts/result/validate` | Final result JSON. |
| `POST` | `/v1/contracts/mq-submission/validate` | Reserved MQ submission JSON. |

Run locally:

```bash
cd training_code_runtime
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8012
python -m unittest discover -s tests -v
```

The runner test deliberately invokes `runner.py` as a subprocess, but no
application endpoint or message consumer can do so yet.

Compose integration is intentionally deferred until the service is stable. Run it
locally or through an explicit temporary deployment only; do not add it to the
default platform compose stack yet.
