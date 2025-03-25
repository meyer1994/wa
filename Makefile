.PHONY: build clean deploy destroy

clean:
	rm -rf dist

build:
	mkdir -p dist
	uv export \
		--frozen \
		--no-dev \
		--no-editable \
		-o 'dist/requirements.txt'
	uv pip install \
		--no-installer-metadata \
		--no-compile-bytecode \
		--python-platform 'x86_64-manylinux2014' \
		--python '3.13' \
		--target 'dist' \
		-r 'dist/requirements.txt'
	cp -rfv wa dist/
	cp -v handler.py dist/
	cd dist && zip -r lambda.zip .


deploy:
	npx aws-cdk deploy --app 'uv run infra.py' --verbose


destroy:
	npx aws-cdk destroy --app 'uv run infra.py' --verbose

