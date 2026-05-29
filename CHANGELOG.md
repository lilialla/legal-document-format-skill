# 更新日志

本项目遵循语义化版本思路记录公开发布变化。

## 1.0.0 - 2026-05-29

### 新增

- 发布版强制视觉校验：完整发布档必须具备 LibreOffice `soffice` 和 Poppler `pdftoppm`。
- `check_release_requirements.py`：检查 Python、LibreOffice 和 Poppler 是否满足发布档要求。
- `release_smoke.py`：一键运行 V1 发布 smoke gate，包括依赖、脚本语法、Python 编译、synthetic DOCX、DOCX 渲染、`--require-visual`/`--fail-on-warning` 格式门禁和测试。
- 并行渲染防护：`render_docx.sh` 为每次 LibreOffice 渲染使用独立 profile，`release_smoke.py` 覆盖 3 路并行渲染。
- PNG 内容差异检查：`compare_rendered_pages.py` 增加文件哈希差异 warning，避免同尺寸同大小不同内容被误判为通过。
- `format_gate.py --require-visual`：缺少 baseline/candidate PNG 渲染页时直接失败。
- `project-basis.md`：沉淀内部文书格式经验的公开抽象版，并说明不公开真实案件和私有模板。
- 现代中文 README 首页、Logo、Badges、Topics、分发档位、隐私安全和外部参考说明。

### 验证

- 当前 V1 本地验证：`51 passed`。
- 发布 smoke gate 已覆盖 DOCX -> PDF -> PNG 渲染链路。

### 边界

- 本项目提供格式质量门禁和 Agent Skill 规则，不提供法律意见，也不替代律师审阅。
- 像素级 PDF diff 作为增强项保留，不作为 V1 默认依赖。
