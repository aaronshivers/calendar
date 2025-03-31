- name: Run tests with coverage
  run: poetry run coverage run -m unittest discover -s tests
- name: Generate coverage report
  run: poetry run coverage report