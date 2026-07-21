Setup to run auto_apply.py on GitHub Actions

1) Create a base64-encoded `state.json` and add as a repo secret named `STATE_JSON_B64`.

Windows (PowerShell):
```
python -c "import base64;print(base64.b64encode(open('state.json','rb').read()).decode())" > state.b64
# copy contents of state.b64 into the GitHub secret
```

Linux/macOS:
```
python3 -c "import base64,sys;print(base64.b64encode(open('state.json','rb').read()).decode())" > state.b64
```

2) Commit these files to your repository and push.
3) On GitHub: Settings → Secrets → Actions → New repository secret → name: `STATE_JSON_B64`, value: paste the base64 string.
4) The workflow `.github/workflows/auto_apply.yml` runs at 02:00 and 14:00 UTC every day. You can also trigger it manually from the Actions tab.

Notes:
- `applied_jobs.txt` is stored in the repository working directory. The workflow will attempt to commit `applied_jobs.txt` back to the repo when it changes using the default `GITHUB_TOKEN` credentials. If your branch is protected or the token lacks push permissions, you may need to create a Personal Access Token (PAT) with `repo` scope and store it as a secret named `PAT` then update the workflow to use it.
- Sessions may expire; if login fails, recreate `state.json` and update the secret.
- Confirm this automation complies with Naukri and employer terms before wide use.
