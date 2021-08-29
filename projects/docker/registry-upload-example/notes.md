Assumptions:
- Would be good if source is reachable by something with docker but it's not
  necessary. However, you will need access to the layers/blobs somehow e.g. via
  http requests or artefactory.
- Destination should be reachable by something with docker.

**Source and Destination have docker**

If source has docker then we can do a `docker save` to save the image and hurl
it to the destination and do a `docker load` to load it back and we're done.
Otherwise, read further...


**Only Destination has docker**

1. Get blobs and artefacts from a repository e.g. via cURL or similar to access
   APIs to download the blobs.
2. Host a docker registry on a destination VM: https://docs.docker.com/registry/
3. Download the blobs from the source repository onto destination VM.
4. Upload the layer/config blobs.
     - Example script: `push_layers.sh`. Modify based on your own structure of
       data.
   > Note: The layers always have to be uploaded first.
5. Upload the manifest.
    - Example script: `push_manifest.sh`. Modify based on your own structure of
      data.
6. pull image using `docker pull localhost:5000/<image_name>`
7. run the container using `docker run -it localhost:5000/<image_name> bash` or
   similar


**To run the image with a gitlab runner**

https://docs.gitlab.com/runner/install/docker.html

1. Initialize a dummy repo and commit the .gitlab-ci.yml. This is needed
   because gitlab-runner only runs on committed ci files.
2. Create a docker container as per the gitlab runner installation instructions
   and also mount the repo directory (in this case assuming it's PWD:)
   ```sh
     docker run -d \
       --name gitlab-runner \
       --restart always \
       -v $PWD:$PWD \
       -v /var/run/docker.sock:/var/run/docker.sock \
     gitlab/gitlab-runner:latest
   ```
   > Note: we also need to make sure that docker.sock is mounted so that the
   > container we plan to run within the runner can be a sibling container
3. Run the pipeline stage:
   ```sh
     docker exec -it \
       -w $PWD \
       gitlab-runner \
       gitlab-runner exec docker test
   ```
   - Execute in directory $PWD inside the container `gitlab-runner` the command
     `gitlab-runner exec docker test` which tells the gitlab runner to execute
     the pipeline stage `test` in a docker container.
   > Note: the base image should be defined in the `.gitlab-ci.yml`

Other notes:
- you may need to set `config.toml` which might be in `/etc/gitlab-runner/` to
  set allowed images.
- For example:
  ```conf
    [[runners]]
    [runners.docker]
    allowed_images = "locahost:5000/<image_name>"
    # --- for services to run with the job ---
    [[runners.docker.services]]
    name = "mysql:latest"
  ```
