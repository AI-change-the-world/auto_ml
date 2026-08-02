# Training Model Package Template

This ZIP is the controlled import format for a user-supplied base model or a
previous training state. It does **not** contain training code and is never
executed during validation or registration.

```text
my-model-package.zip
├── training_model_package.json
├── weights/model.pt
└── checkpoints/last.pt          # Optional; only this makes `resume` available
```

`artifact_path` is an initialization weight. It may be used with
`model_input.mode: "initialize"`. `resume_checkpoint_path` is optional and
must name a distinct file that includes all state required by the declared
framework to continue training. Only a registered `resume_checkpoint_path` may
be submitted with `model_input.mode: "resume"`.

The model package must declare an exact framework identity, task kind, class
order, and artifact format. A training package accepts it only when its
`model_input_contract` declares the same framework and format. The runtime
stores the uploaded ZIP plus the selected individual artifact(s) as immutable
objects in the existing models bucket; MQ carries object references, never ZIP
bytes or direct storage credentials.
