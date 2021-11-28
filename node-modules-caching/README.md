# Node modules caching test

A POC to cache node_modules directory as a build Artifact.
Instead of `npm install`ing dependencies in each and every job

* install them once in "setup" job
* store as a build artifact
* download the build artifact in next jobs.

# Description

The full workflow file can be found in [node-modules-caching_build-and-test.yml](../.github/workflows/node-modules-caching_build-and-test.yml).

## Install and cache dependencies

The `npm-install-and-cache` job installs NPM dependencies and stores then as a build Artifact.
Other jobs that require node_modules will wait for this job to finish.

The NPM install step creates the node_modules directory with installed dependencies:

```yml
- name: 'Install deps'
  run: npm ci
```

The node_modules directory is then put into a tar ball to reduce the amount of individual files to store in artifacts, since the amount of files in a node_modules directory is substantial.
Taring also preserves file permissions and file name cases.
See [Limitations](https://github.com/actions/upload-artifact#limitations) section in `actions/upload-artifact` for more details.

```yml
- name: 'Tar node_modules'
  run: tar cvf node_modules.tar node_modules

- name: 'Compress node_modules tar'
  run: bzip2 -9 node_modules.tar
```

The two steps could be combined into one.
But this gives more explicit output in Actions console what step failed if something failed.
Also note that you probably want to remove the `v` option from tar command when node_modules gets bigger to avoid excess logging.

The zipped node_modules is then uploaded as an artifact:

```yml
- name: 'Cache node_modules as Artifact'
  uses: actions/upload-artifact@v2
  with:
    name: node-modules-cache-${{ github.run_id }}
    path: node-modules-caching/node_modules.tar.bz2
    if-no-files-found: error
    retention-days: 1
```

`${{ github.run_id }}` appended to artifact name is a unique number for each run within a repository.
In this case it is used to create a unique cache for each workflow run.
This number does not change if you re-run the workflow run, in which case the old artifact just gets overwritten.

Retention setting is set to a minimum value, since we need the cached node_modules only in single workflow run.

## Restore cached dependencies

First of all, the jobs that depend on node_modules should wait for the `npm-install-and-cache` job to finish.
This is achieved with `needs: npm-install-and-cache`.

```yml
capitalize1:
  name: capitalize1
  needs: npm-install-and-cache
```

The cached node_modules is then downloaded from artifacts, unzipped and untarred.

```yml
- name: 'Restore node_modules cache'
  uses: actions/download-artifact@v2
  with:
    name: node-modules-cache-${{ github.run_id }}
    path: node-modules-caching

- name: 'Uncompress node_modules tar'
  run: bunzip2 -v node_modules.tar.bz2

- name: 'Untar node_modules'
  run: tar xvf node_modules.tar
```

# Things to consider

`node_modules` directory can easily be several hundred megabytes in size.
Zipping will make it considerably smaller.
However, when running the workflow several times within the one day retention period, you might hit the GitHub storage [limit](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions#included-storage-and-minutes).
