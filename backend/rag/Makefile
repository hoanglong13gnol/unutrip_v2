.PHONY: clean install install-dev lint typecheck test test-fast quality fetch-artifacts package-artifacts eval-golden-ci eval-golden-full

clean:
	python scripts/clean_dev_artifacts.py

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check app core domain generation llm pipelines providers retrieval services tests scripts

typecheck:
	python -m mypy --explicit-package-bases \
	  -p core -p domain -p generation -p providers -p pipelines -p repositories \
	  -p retrieval -p app

test-fast:
	python -m pytest tests/ -q --no-cov

test:
	python jobs/build_rag_artifacts.py --from-fixture
	python -m pytest tests/ -q

quality: lint typecheck test
	python scripts/verify_rag_artifacts.py --strict

fetch-artifacts:
	python scripts/fetch_rag_artifacts.py

package-artifacts:
	python jobs/package_rag_artifacts.py

eval-golden-ci:
	python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
	  --require-labels --min-hit-at5 0.5 --min-province-accuracy 1.0

eval-golden-full:
	python scripts/eval_rag_retrieval.py --golden eval/golden_queries.json --ci \
	  --min-province-accuracy 1.0 --min-hit-at5 0.75
