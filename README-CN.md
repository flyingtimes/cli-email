# Email Priority Manager - 邮件优先级管理器

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 项目简介

Email Priority Manager 是一个功能强大的命令行邮件管理工具，专为中文用户设计。它利用人工智能技术自动对邮件进行优先级分类和智能管理，帮助用户高效处理大量邮件。

## 主要功能

### 🤖 智能邮件分类
- 基于 BigModel.cn AI 模型的智能邮件分类
- 自动识别邮件优先级：紧急、高、中、低
- 智能分类邮件类别：工作、个人、财务、购物等
- 支持中文邮件内容的深度理解

### 📧 邮件管理功能
- 邮件扫描和检索
- 邮件列表显示和筛选
- 邮件搜索和查询
- 标签管理和分类
- 邮件导出功能

### 🔍 智能搜索
- 自然语言搜索
- 按发件人、主题、内容搜索
- 高级筛选功能
- 搜索结果高亮显示

### 📊 数据统计
- 邮件统计概览
- 优先级分布分析
- 分类统计报告
- 时间趋势分析

### 🛠️ 系统管理
- 配置文件管理
- 数据库初始化和迁移
- API 密钥管理
- 系统状态检查

## 安装指南

### 系统要求
- Python 3.8 或更高版本
- 支持 IMAP/POP3 的邮箱账户
- 网络连接（用于 AI 功能）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/email-priority-manager.git
   cd email-priority-manager
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **初始化系统**
   ```bash
   python -m src.email_priority_manager.cli.main setup init
   ```

5. **配置邮箱设置**
   ```bash
   python -m src.email_priority_manager.cli.main setup config --interactive
   ```

6. **设置 API 密钥**
   ```bash
   python -m src.email_priority_manager.cli.main setup secrets
   ```

## 配置说明

### 邮箱配置
编辑 `config.yaml` 文件：

```yaml
email:
  server: "imap.your-provider.com"  # 邮件服务器地址
  port: 993                          # 端口号
  username: "your-email@example.com" # 邮箱用户名
  password: "your-password"          # 邮箱密码或授权码
  use_ssl: true                      # 是否使用 SSL
```

### AI 配置
```yaml
ai:
  bigmodel_api_key: "your-api-key"   # BigModel.cn API 密钥
  bigmodel_enabled: true             # 启用 AI 功能
  bigmodel_model: "glm-4"             # 使用的模型
  max_tokens: 1000                   # 最大令牌数
  temperature: 0.7                   # 创造性参数
```

### 数据库配置
```yaml
database:
  path: "emails.db"                  # 数据库文件路径
  backup_enabled: true               # 启用备份
  backup_interval: 86400            # 备份间隔（秒）
```

## 使用指南

### 基本命令

#### 系统设置
```bash
# 初始化系统
python -m src.email_priority_manager.cli.main setup init

# 配置系统
python -m src.email_priority_manager.cli.main setup config

# 设置密钥
python -m src.email_priority_manager.cli.main setup secrets

# 检查状态
python -m src.email_priority_manager.cli.main setup status
```

#### 邮件扫描
```bash
# 扫描邮箱
python -m src.email_priority_manager.cli.main scan mailbox

# 快速扫描
python -m src.email_priority_manager.cli.main scan quick

# 全面扫描
python -m src.email_priority_manager.cli.main scan full

# 检查连接状态
python -m src.email_priority_manager.cli.main scan status
```

#### 邮件分类
```bash
# 分类所有邮件
python -m src.email_priority_manager.cli.main classify all

# 分类未读邮件
python -m src.email_priority_manager.cli.main classify unread

# 重新分类
python -m src.email_priority_manager.cli.main classify reclassify
```

#### 邮件列表
```bash
# 列出所有邮件
python -m src.email_priority_manager.cli.main list emails

# 列出紧急邮件
python -m src.email_priority_manager.cli.main list urgent

# 列出未读邮件
python -m src.email_priority_manager.cli.main list unread

# 列出最近邮件
python -m src.email_priority_manager.cli.main list recent

# 搜索邮件
python -m src.email_priority_manager.cli.main list search "关键词"
```

#### 自然语言查询
```bash
# 交互式查询
python -m src.email_priority_manager.cli.main query

# 快速查询
python -m src.email_priority_manager.cli.main query "最近的紧急邮件"

# 统计查询
python -m src.email_priority_manager.cli.main query "邮件统计"
```

#### 杂项功能
```bash
# 标签管理
python -m src.email_priority_manager.cli.main tag add
python -m src.email_priority_manager.cli.main tag remove
python -m src.email_priority_manager.cli.main tag list

# 配置管理
python -m src.email_priority_manager.cli.main config show
python -m src.email_priority_manager.cli.main config set

# 导出功能
python -m src.email_priority_manager.cli.main export csv
python -m src.email_priority_manager.cli.main export json

# 统计报告
python -m src.email_priority_manager.cli.main stats
```

### 高级功能

#### 批量操作
```bash
# 批量分类
python -m src.email_priority_manager.cli.main classify batch --limit 100

# 批量导出
python -m src.email_priority_manager.cli.main export batch --format csv
```

#### 高级筛选
```bash
# 按优先级筛选
python -m src.email_priority_manager.cli.main list emails --priority urgent

# 按时间筛选
python -m src.email_priority_manager.cli.main list emails --since-days 7

# 按发件人筛选
python -m src.email_priority_manager.cli.main list emails --sender "boss@company.com"
```

#### 智能搜索
```bash
# 自然语言搜索
python -m src.email_priority_manager.cli.main query "昨天收到的关于项目的邮件"

# 统计查询
python -m src.email_priority_manager.cli.main query "这周的邮件数量"

# 组合查询
python -m src.email_priority_manager.cli.main query "来自张三的紧急邮件"
```

## 支持的邮箱服务商

### 国内邮箱
- **QQ邮箱**: imap.qq.com (993)
- **163邮箱**: imap.163.com (993)
- **126邮箱**: imap.126.com (993)
- **新浪邮箱**: imap.sina.com (993)
- **中国移动邮箱**: imap.chinamobile.com (993)

### 国外邮箱
- **Gmail**: imap.gmail.com (993)
- **Outlook**: outlook.office365.com (993)
- **Yahoo**: imap.mail.yahoo.com (993)
- **iCloud**: imap.mail.me.com (993)

## 故障排除

### 常见问题

#### 1. 邮箱连接失败
**问题**: 无法连接到邮件服务器
**解决**:
- 检查邮箱设置是否正确
- 确认是否启用了 IMAP 服务
- 检查网络连接
- 验证用户名和密码

#### 2. AI 功能不可用
**问题**: BigModel.cn API 调用失败
**解决**:
- 检查 API 密钥是否正确
- 确认网络连接正常
- 检查 API 配额是否充足
- 验证模型名称是否正确

#### 3. 数据库错误
**问题**: 数据库初始化失败
**解决**:
- 检查数据库文件权限
- 确认磁盘空间充足
- 尝试重新初始化数据库
- 检查 SQLite 版本兼容性

#### 4. 中文显示问题
**问题**: 中文邮件内容显示异常
**解决**:
- 确认终端支持 UTF-8 编码
- 检查系统语言设置
- 使用支持中文的终端软件
- 更新 Python 环境

### 调试模式

启用详细日志：
```bash
python -m src.email_priority_manager.cli.main --debug <command>
```

查看日志文件：
```bash
tail -f logs/email_priority_manager.log
```

## 开发指南

### 项目结构
```
email-priority-manager/
├── src/email_priority_manager/
│   ├── cli/                     # 命令行界面
│   │   ├── commands/           # 命令模块
│   │   ├── utils/              # 工具函数
│   │   └── framework/          # 框架代码
│   ├── core/                   # 核心功能
│   │   ├── email_client.py     # 邮件客户端
│   │   ├── classifier.py       # 邮件分类器
│   │   └── processor.py        # 邮件处理器
│   ├── ai/                     # AI 功能
│   │   ├── bigmodel.py         # BigModel 客户端
│   │   └── nlp.py              # 自然语言处理
│   ├── config/                 # 配置管理
│   │   ├── settings.py         # 设置管理
│   │   └── secrets.py          # 密钥管理
│   └── database/               # 数据库
│       ├── models.py           # 数据模型
│       └── migrations.py       # 数据库迁移
├── config.yaml                  # 配置文件
├── emails.db                   # 数据库文件
└── logs/                       # 日志目录
```

### 贡献指南

1. **Fork 项目**
2. **创建功能分支**
   ```bash
   git checkout -b feature/new-feature
   ```
3. **提交更改**
   ```bash
   git commit -am "Add new feature"
   ```
4. **推送分支**
   ```bash
   git push origin feature/new-feature
   ```
5. **创建 Pull Request**

### 代码规范

- 使用 PEP 8 代码风格
- 编写详细的文档字符串
- 添加类型注解
- 编写单元测试
- 遵循 Git 提交规范

## 版本历史

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 基础邮件管理功能
- AI 驱动的邮件分类
- 中文用户界面
- 自然语言查询功能

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 支持

如果您在使用过程中遇到问题或有任何建议，请：

1. 查看 [故障排除](#故障排除) 部分
2. 提交 [Issue](https://github.com/your-username/email-priority-manager/issues)
3. 查看 [Wiki](https://github.com/your-username/email-priority-manager/wiki)
4. 发送邮件至：support@example.com

## 致谢

感谢以下开源项目的支持：
- [Click](https://click.palletsprojects.com/) - 命令行界面框架
- [Rich](https://github.com/Textualize/rich) - 终端美化库
- [SQLAlchemy](https://www.sqlalchemy.org/) - 数据库 ORM
- [BigModel.cn](https://open.bigmodel.cn/) - AI 模型服务

---

**Email Priority Manager** - 让邮件管理更智能、更高效！ 🚀