# Use and cite Modelstamp in research

This page provides a complete, copy-ready path for using Modelstamp in a
research workflow. You can install the package, create and verify an artifact,
record the result, and cite the software without contacting the maintainer.

## 1. Install a fixed release

Create a fresh environment and install the release used in your study:

```bash
python -m venv .venv
```

### macOS or Linux

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install modelstamp==0.1.5
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install modelstamp==0.1.5
```

Record the interpreter and installed packages with the experiment:

```bash
python --version
python -m pip show modelstamp
python -m pip freeze > requirements-modelstamp.txt
```

## 2. Save and verify an artifact

This minimal example has no machine-learning framework dependency:

```python
import modelstamp as ms

model = {
    "feature_names": ["age", "income"],
    "weights": [0.3, 0.7],
}

manifest = ms.save(
    model,
    "model.pkl",
    metadata={
        "study": "example-study",
        "dataset": "dataset-version-or-doi",
    },
)

# This verifies the artifact without deserializing it.
ms.verify("model.pkl")

# Refuse to deserialize if the represented environment differs.
restored, manifest = ms.load("model.pkl", on_mismatch="raise")

print(restored)
print(manifest.relevant_packages)
```

Saving creates `model.pkl` and `model.pkl.manifest.json`. Preserve both files
with the replication materials. `ms.verify()` verifies before deserialization;
`on_mismatch="raise"` additionally refuses to load when the represented Python
or relevant-package environment differs.

To inspect a manifest without deserializing the artifact:

```python
manifest = ms.inspect("model.pkl")
report = ms.check("model.pkl")
```

`inspect()` validates manifest structure but does not verify the artifact
checksum or signature. Use `verify()` or `check()` when trust matters.

## 3. Use the command line in an automated workflow

The same pre-load checks are available through the CLI:

```bash
modelstamp inspect model.pkl
modelstamp check model.pkl
modelstamp verify model.pkl
```

If the console script is not on `PATH`, use `python -m modelstamp` instead of
`modelstamp`. In CI, run `modelstamp verify` before the evaluation process loads
the artifact.

## 4. Record the research use

Include the following fields in the paper, repository, or replication archive:

```text
Modelstamp version: 0.1.5
Python version: <version>
Operating system: <name and version>
Artifact format: <pickle or joblib>
Artifact identifier: <filename, repository path, or persistent identifier>
Verification command: <command used>
Environment mismatch policy: <warn, raise, or ignore>
Verification result: <verified, rejected, or differences reported>
Code and artifact archive: <permanent URL or DOI>
```

Archive the experiment code, dependency lockfile, serialized artifact,
Modelstamp manifest, and verification command together. Never publish
proprietary data, credentials, HMAC keys, or sensitive manifest metadata.

## Methods-section wording

Copy and adapt this paragraph:

> We used Modelstamp 0.1.5 to record the serialized machine-learning artifact,
> its SHA-256 digest, and relevant runtime-environment metadata. Before
> deserialization, we verified the artifact and applied the `raise` environment
> mismatch policy. We archived the artifact, sidecar manifest, dependency
> specification, and verification command with the replication materials.

If you used HMAC authentication, add:

> The artifact/manifest pair was authenticated using Modelstamp's HMAC option
> within a shared-secret workflow. The signing key was managed separately and
> was not included in the replication archive.

HMAC authentication does not provide public-key publisher identity and does not
prevent an authorized shared-key holder from creating a new valid pair. See the
[security boundary](security.md) before making a security claim.

## Cite Modelstamp

The repository's [`CITATION.cff`](https://github.com/AnaghaDhekne/modelstamp/blob/main/CITATION.cff)
is the machine-readable source of citation metadata. Cite the exact software
release used in the study and the preprint when it informed the research design
or analysis.

### Software

> Dhekne, A. (2026). *Modelstamp: Pre-deserialization integrity and environment
> verification for persisted Python machine-learning artifacts* (Version
> 0.1.5) [Computer software]. Zenodo.
> https://doi.org/10.5281/zenodo.22047771

```bibtex
@software{dhekne_modelstamp_2026,
  author    = {Dhekne, Anagha},
  title     = {Modelstamp: Pre-deserialization integrity and environment
               verification for persisted Python machine-learning artifacts},
  version   = {0.1.5},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22047771},
  url       = {https://doi.org/10.5281/zenodo.22047771}
}
```

### Preprint

> Dhekne, A. (2026). *Modelstamp: Pre-Deserialization Verification of
> Machine-Learning Artifacts and Runtime Environment State*. arXiv:2609.01781.
> https://arxiv.org/abs/2609.01781

```bibtex
@article{dhekne2026modelstamp,
  author  = {Dhekne, Anagha},
  title   = {Modelstamp: Pre-Deserialization Verification of Machine-Learning
             Artifacts and Runtime Environment State},
  journal = {arXiv preprint arXiv:2609.01781},
  year    = {2026},
  doi     = {10.48550/arXiv.2609.01781},
  url     = {https://arxiv.org/abs/2609.01781}
}
```

## Reproducibility checklist

- [ ] Pin and report the Modelstamp version.
- [ ] Record Python, operating-system, and dependency versions.
- [ ] Archive the artifact together with its `.manifest.json` sidecar.
- [ ] Run verification before deserializing the artifact.
- [ ] State the environment mismatch policy used by the study.
- [ ] Record the verification outcome with the experiment results.
- [ ] Archive the verification command and dependency specification.
- [ ] Cite the software release and, where relevant, the preprint.

## Related documentation

- [Quick start](quickstart.md)
- [CI/CD verification](ci.md)
- [Signing and key rotation](signing.md)
- [Security boundary](security.md)
- [Benchmarks](benchmarks.md)
- [Research and adoption](research-adoption.md)

If your use is public, you may add it to the project's
[public feedback issue](https://github.com/AnaghaDhekne/modelstamp/issues/18).
Public reports are welcome but are not required to use or cite Modelstamp.
