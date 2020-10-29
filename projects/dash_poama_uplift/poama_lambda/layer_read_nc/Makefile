build-ReadNetcdfLayer:
	mkdir -p "$(ARTIFACTS_DIR)/python"
	python -m pip install \
		--no-cache-dir \
		--no-compile \
        --no-deps \
		-r requirements.txt \
		-t "$(ARTIFACTS_DIR)/python"

# build-ReadNetcdfLayer:
# 	mkdir -p "$(ARTIFACTS_DIR)/python"
# 	CFLAGS="-g0 -Wl,--strip-all -I/usr/include:/usr/local/include -L/usr/lib:/usr/local/lib" \
# 	python -m pip install \
# 		--no-cache-dir \
# 		--compile \
# 		--global-option="build_ext" \
# 		-r requirements.txt \
# 		-t "$(ARTIFACTS_DIR)/python"
