# 贡献指南

感谢关注“文格：法律文书格式门禁 Skill”。本仓库是 synthetic-first 的法律文书格式工具，不接收真实案件材料、私有模板或未脱敏客户信息。

## 开发环境

```bash
python3 -m pip install -e ".[test]"
```

完整发布档还需要安装：

```bash
soffice --version
pdftoppm -h
```

## 提交前检查

```bash
bash -n skills/legal-document-format/scripts/render_docx.sh
python3 -m py_compile skills/legal-document-format/scripts/*.py tests/*.py
python3 -m pytest -q
./skills/legal-document-format/scripts/release_smoke.py
```

## 文档规则

- 修改脚本、命令或门禁口径时，同步更新 README、脚本 README 或相邻 reference。
- 不要宣传尚不存在的功能。
- 对外文档统一使用中文。
- 发布档能力必须能被命令、测试或 smoke gate 证明。

## 安全与隐私

不要提交：

- 真实诉状、裁决书、合同、证据或往来函件；
- 客户名称、案号、金额、商业秘密或未公开事实；
- 私有机构模板；
- 商业平台导出记录；
- 密钥、令牌、cookie 或本地账号配置。

如发现敏感信息已进入仓库，请停止继续提交，先按 `SECURITY.md` 的方式处理。
