# Release Checklist / 发布清单

## English

### 1. Pre-release checks

1. Ensure branch is clean: `git status`
2. Run tests:
   - `python -m unittest discover -s tests -p 'test_*.py' -v`
3. Run import smoke check:
   - `PYTHONPATH=src python -m funasr_long_audio_safe.cli --help`
4. Verify docs are up to date:
   - `README.md`
   - `docs/setup.md`
   - `docs/architecture.md`

### 2. Version update

1. Update version in `pyproject.toml` (`[project].version`)
2. Update `src/funasr_long_audio_safe/__init__.py` (`__version__`)
3. Commit:
   - `git commit -am "chore(release): vX.Y.Z"`

### 3. Build artifacts

1. Install build tool:
   - `python -m pip install --upgrade build twine`
2. Build package:
   - `python -m build`
3. Verify package metadata:
   - `python -m twine check dist/*`

### 4. Publish to PyPI

1. TestPyPI (optional):
   - `python -m twine upload --repository testpypi dist/*`
2. PyPI:
   - `python -m twine upload dist/*`
3. Verify install:
   - `python -m pip install -U funasr-long-audio-safe`

### 5. GitHub release

1. Tag:
   - `git tag vX.Y.Z`
2. Push commits and tags:
   - `git push origin main --tags`
3. Create GitHub Release with notes:
   - major changes
   - breaking changes
   - migration notes

## 中文

### 1. 发布前检查

1. 确认工作区干净：`git status`
2. 运行测试：
   - `python -m unittest discover -s tests -p 'test_*.py' -v`
3. 运行导入冒烟：
   - `PYTHONPATH=src python -m funasr_long_audio_safe.cli --help`
4. 检查文档是否同步：
   - `README.md`
   - `docs/setup.md`
   - `docs/architecture.md`

### 2. 版本号更新

1. 修改 `pyproject.toml` 的 `[project].version`
2. 修改 `src/funasr_long_audio_safe/__init__.py` 的 `__version__`
3. 提交版本变更：
   - `git commit -am "chore(release): vX.Y.Z"`

### 3. 构建产物

1. 安装构建工具：
   - `python -m pip install --upgrade build twine`
2. 构建包：
   - `python -m build`
3. 校验包元数据：
   - `python -m twine check dist/*`

### 4. 发布到 PyPI

1. 可选先发 TestPyPI：
   - `python -m twine upload --repository testpypi dist/*`
2. 发布正式 PyPI：
   - `python -m twine upload dist/*`
3. 验证安装：
   - `python -m pip install -U funasr-long-audio-safe`

### 5. GitHub Release

1. 打标签：
   - `git tag vX.Y.Z`
2. 推送主分支与标签：
   - `git push origin main --tags`
3. 在 GitHub 创建 Release，建议包含：
   - 主要改动
   - 破坏性变更
   - 升级迁移说明
