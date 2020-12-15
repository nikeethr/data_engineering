build-ReadNetcdfLayer:
	mkdir -p "$(ARTIFACTS_DIR)/python" && \
	python -m pip install \
		--no-cache-dir \
		--no-compile \
		--no-deps \
		-r requirements.txt \
		-t "$(ARTIFACTS_DIR)/python" && \
	rm -rf "$(ARTIFACTS_DIR)/python/bokeh*" ||: && \
	rm -rf "$(ARTIFACTS_DIR)/python/boto3*" ||: && \
	rm -rf "$(ARTIFACTS_DIR)/python/botocore*" ||: && \
	rm -rf "$(ARTIFACTS_DIR)/python/datashader/examples" ||: && \
	rm -rf "$(ARTIFACTS_DIR)/python/pandas/tests" ||:

