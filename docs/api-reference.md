# API 参考文档

本文档描述了检测智能体非活跃账号 CLI 工具所使用的后端 API 接口。

## 接口概述

| 接口 | Action | Service | 用途 |
|------|--------|---------|------|
| ListApp | `ListApp` | app | 获取智能体列表（含创建人） |
| ListUserForAdmin | `ListUserForAdmin` | iam | 获取平台用户列表 |
| DeleteUser | `DeleteUser` | iam | 删除指定用户 |

## 通用说明

### 认证方式
所有接口使用火山引擎签名 v4 进行认证。

### 请求格式
- Method: POST
- Content-Type: application/json
- URL 参数: Action, Version, X-Account-Id

### Top 参数（可选）
请求中的顶层公共参数，默认不传：
```json
{
  "Top": {
    "RequestID": "可选，请求唯一标识",
    "TenantID": "可选，租户ID",
    "UserID": "可选，用户ID",
    "RegionKey": "可选，区域ID"
  }
}
```

### 分页
ListApp 和 ListUserForAdmin 接口支持分页，通过 ListOpt 参数控制：
- PageNumber: 页码（从 1 开始）
- PageSize: 每页条数（默认 10000）

### 默认配置
- ListApp: 默认 PageSize=10000，Filter 包含 StartTime/EndTime 时间范围
- ListUserForAdmin: 默认 PageSize=10000，IncludeVisitor=false
- DeleteUser: 无分页

---

## ListApp - 获取智能体列表

**Service**: `app`

### 请求（默认配置）
```json
{
  "Filter": {
    "StartTime": "2020-01-01T00:00:00.00Z",
    "EndTime": "2100-01-01T00:00:00.00Z"
  },
  "ListOpt": {
    "PageNumber": 1,
    "PageSize": 10000
  }
}
```

### 请求（带可选参数）
```json
{
  "Filter": {
    "StartTime": "2020-01-01T00:00:00.00Z",
    "EndTime": "2100-01-01T00:00:00.00Z",
    "Keyword": "可选，搜索关键词",
    "AppType": 0,
    "Status": 1,
    "WorkspaceID": "可选，工作空间ID"
  },
  "ListOpt": {
    "PageNumber": 1,
    "PageSize": 10000
  }
}
```

### 响应
```json
{
  "Response": {
    "Items": [
      {
        "AppID": "智能体ID",
        "Name": "智能体名称",
        "Description": "描述",
        "Icon": "图标URL",
        "AppType": 0,
        "Status": 1,
        "CreateTime": "2024-01-01T00:00:00Z",
        "CreateUser": "创建人ID",
        "WorkspaceID": "工作空间ID",
        "IsFavorite": false,
        "PublishStatus": 1
      }
    ],
    "Total": 100
  }
}
```

### AppType 枚举值
| 值 | 说明 |
|----|------|
| 0 | Single - 单Agent模式 |
| 1 | Multi - 多Agent模式 |
| 2 | ChatFlow - 对话流模式 |
| 3 | Workflow - 流程编排模式 |

---

## ListUserForAdmin - 获取用户列表

**Service**: `iam`

### 请求（默认配置）
```json
{
  "IncludeVisitor": false,
  "ListOpt": {
    "PageNumber": 1,
    "PageSize": 10000
  }
}
```

### 请求（带可选参数）
```json
{
  "Query": "可选，搜索关键词",
  "Status": 1,
  "RoleName": "可选，角色名",
  "OrgID": "可选，组织ID",
  "IncludeVisitor": false,
  "Source": "可选，用户来源",
  "ContactSearch": "可选，手机号/邮箱搜索",
  "ListOpt": {
    "PageNumber": 1,
    "PageSize": 10000
  }
}
```

### 响应
```json
{
  "Response": {
    "Items": [
      {
        "ID": "用户ID",
        "UserName": "用户名",
        "DisplayName": "显示名",
        "Email": "邮箱",
        "Mobile": "手机号",
        "Source": "用户来源",
        "Status": 1,
        "RoleName": "角色名",
        "TenantID": "租户ID",
        "TenantName": "租户名称",
        "Orgs": [
          {"OrgID": "组织ID", "RoleName": "组织角色"}
        ],
        "UserGroups": [
          {"UserGroupID": "用户组ID", "UserGroupName": "用户组名"}
        ],
        "HasPassword": true,
        "Creator": "创建人",
        "CreatedTime": "2024-01-01T00:00:00Z",
        "UpdatedTime": "2024-01-01T00:00:00Z"
      }
    ],
    "Total": 1000
  }
}
```

---

## DeleteUser - 删除用户

**Service**: `iam`

### 请求方式 1: 通过 ID 删除
```json
{
  "ID": "用户ID"
}
```

### 请求方式 2: 通过用户名删除
```json
{
  "Name": "用户名"
}
```

### 响应
无返回内容（成功时返回空响应）

### 错误码
| 错误码 | 说明 |
|--------|------|
| 1001 | 用户不存在 |
| 1002 | 无权限删除 |
| 1003 | 用户受保护无法删除 |

---

## 签名机制

### 服务与签名对应关系

| 接口 | Service | Region |
|------|---------|--------|
| ListApp | app | cn-north-1 |
| ListUserForAdmin | iam | cn-north-1 |
| DeleteUser | iam | cn-north-1 |

### Python 示例

#### ListApp 签名
```python
from volcengine.auth.SignerV4 import SignerV4
from volcengine.auth.SignParam import SignParam
from volcengine.Credentials import Credentials
from collections import OrderedDict
import requests
import json

# 配置
ak = "your_access_key"
sk = "your_secret_key"
region = "cn-north-1"
service = "app"  # ListApp 使用 app service
host = "10.10.160.222:30040/"
action = "ListApp"
version = "2023-08-01"
account_id = "1000000000"

# 签名
signer = SignerV4()
param = SignParam()
param.method = "POST"
param.host = host

query = OrderedDict()
query["Action"] = action
query["Version"] = version
query["X-Account-Id"] = account_id
param.query = query

header = OrderedDict()
header["Host"] = host
header["Content-Type"] = "application/json"
param.header_list = header
param.headers = header

credentials = Credentials(ak, sk, service, region)
signer.sign(param, credentials)

# 发送请求
url = f"http://{host}?Action={action}&Version={version}&X-Account-Id={account_id}"
data = {
    "Filter": {
        "StartTime": "2020-01-01T00:00:00.00Z",
        "EndTime": "2100-01-01T00:00:00.00Z"
    },
    "ListOpt": {"PageNumber": 1, "PageSize": 10000}
}
response = requests.post(url, headers=param.headers, data=json.dumps(data))
```

#### ListUserForAdmin/DeleteUser 签名
```python
from volcengine.auth.SignerV4 import SignerV4
from volcengine.auth.SignParam import SignParam
from volcengine.Credentials import Credentials
from collections import OrderedDict
import requests
import json

# 配置
ak = "your_access_key"
sk = "your_secret_key"
region = "cn-north-1"
service = "iam"  # ListUserForAdmin 和 DeleteUser 使用 iam service
host = "10.10.160.222:30040/"
action = "ListUserForAdmin"  # 或 "DeleteUser"
version = "2023-08-01"
account_id = "1000000000"

# 签名
signer = SignerV4()
param = SignParam()
param.method = "POST"
param.host = host

query = OrderedDict()
query["Action"] = action
query["Version"] = version
query["X-Account-Id"] = account_id
param.query = query

header = OrderedDict()
header["Host"] = host
header["Content-Type"] = "application/json"
param.header_list = header
param.headers = header

credentials = Credentials(ak, sk, service, region)
signer.sign(param, credentials)

# 发送请求
url = f"http://{host}?Action={action}&Version={version}&X-Account-Id={account_id}"
data = {"IncludeVisitor": False, "ListOpt": {"PageNumber": 1, "PageSize": 10000}}
response = requests.post(url, headers=param.headers, data=json.dumps(data))
```

---

## 环境变量配置

```bash
# API 配置
API_HOST=10.10.160.222:30040/
API_VERSION=2023-08-01
API_REGION=cn-north-1
ACCOUNT_ID=1000000000

# 认证凭据
API_AK=your_access_key_here
API_SK=your_secret_key_here

# Top 参数（可选）
API_REQUEST_ID=your_request_id
API_USER_ID=your_user_id
API_TENANT_ID=your_tenant_id
API_REGION_KEY=your_region_key

# 应用配置
LOG_DIR=logs
DEFAULT_PAGE_SIZE=10000
```