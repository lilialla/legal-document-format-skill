# V1 发布说明

## 发布定位

`1.0.0` 是“文格：法律文书格式门禁 Skill”的首个 V1 可发布版。它面向本地 Agent Skill 分发、公开展示和法律文书格式 QA，不提供法律意见，也不替代律师审阅。

## V1 必须满足

- README 首页中文化，包含 Logo、Badges、Topics、快速开始、能力矩阵、发布版强制校验、项目经验、外部参考、隐私安全和路线图。
- `pyproject.toml` 版本为 `1.0.0`。
- 完整发布档强制安装 Python 3.9+、LibreOffice 和 Poppler。
- `format_gate.py --require-visual` 能阻断缺少视觉渲染页的发布门禁。
- `release_smoke.py` 能跑通 synthetic DOCX 生成、渲染和聚合门禁。
- LibreOffice 渲染使用独立 profile，并通过 3 路并行渲染 smoke。
- PNG 渲染页比较会检查页面文件哈希差异。
- 测试通过，且不依赖真实案件、客户材料或私有模板。

## 发布前命令

```bash
python3 -m pip install -e ".[test]"
./skills/legal-document-format/scripts/check_release_requirements.py --mode release
./skills/legal-document-format/scripts/release_smoke.py
```

## 当前 V1 证据

- 依赖门禁：Python、LibreOffice、Poppler 均通过。
- 自动化测试：`51 passed`。
- smoke gate：`release_smoke.py` 覆盖发布版关键链路。
- 远端分支：`main`。

## 不纳入 V1 默认范围

- 第三方像素级 PDF diff 默认集成；
- 私有模板；
- 真实案件 fixture；
- 托管服务；
- 法律实体内容正确性判断。
