# 空间、用户组织管理接口 - DeleteUser & ListUserForAdmin（含全量关联结构体）
## 一、DeleteUser - 删除用户
### 基础信息
- **Action**：DeleteUser
- **Method**：Post
- **所属模块**：用户管理（user）

### 请求参数（user.DeleteUserRequest）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| ID | string | 二选一 | 用户ID |
| Name | string | 二选一 | 用户名 |
| Top | base.TopParam | true | 顶层公共参数 |

### 响应参数（user.DeleteUserResponse）
无返回结构体

---

## 二、ListUserForAdmin - 管理员获取用户列表
### 基础信息
- **Action**：ListUserForAdmin
- **Method**：Post
- **所属模块**：用户管理（user）

### 请求参数（user.ListUserRequest）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Query | string | false | 支持用户名、显示名模糊查询 |
| Status | byte | false | 用户状态 |
| RoleName | string | false | 角色名称；Custom=自定义角色过滤；Default=默认角色过滤 |
| OrgID | string | false | 组织ID |
| IncludeVisitor | bool | false | 是否包含访客 |
| Source | string | false | 用户来源 |
| ContactSearch | string | false | 支持手机号、邮箱查询 |
| ListOpt | common.ListOption | false | 分页与排序参数 |
| Top | base.TopParam | true | 顶层公共参数 |

### 响应参数（user.ListUserResponse）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Items | list[user.User] | true | 用户信息列表 |
| Total | i64 | true | 数据总条数 |

---

## 三、关联参数结构体（全量）
### 1. base.TopParam（顶层公共参数）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| RequestID | string | true | 请求的RequestId |
| TenantID | string | true | 租户ID |
| UserID | string | true | 子账号ID，可访问租户授权资源 |
| RegionKey | string | true | 区域ID |
| DestService | string | true | 请求的目的服务 |
| DestAction | string | true | 请求的目的服务Action |
| Version | string | true | 请求的版本 |
| RealIp | string | false | 请求的真实IP |
| IdentityType | string | true | 请求的身份类型 |
| AcceptLanguage | string | false | 请求的语言 |

### 2. common.ListOption（分页排序参数）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| Sort | list[common.Sorter] | false | 排序字段 |
| PageNumber | i64 | false | 页码，默认1，必须大于0 |
| PageSize | i64 | false | 每页条数，默认10，必须大于0 |

### 3. common.Sorter（排序规则）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| SortField | string | true | 排序字段（snake_case格式） |
| SortOrder | string | false | 排序顺序，默认desc，可选desc/asc |

### 4. user.User（用户详情结构体）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| ID | string | true | 用户ID |
| Creator | string | true | 创建人 |
| Updater | string | true | 更新人 |
| CreatedTime | string | true | 创建时间 |
| UpdatedTime | string | true | 更新时间 |
| TenantID | string | true | 租户ID |
| TenantName | string | true | 租户名称 |
| UserName | string | true | 用户名 |
| DisplayName | string | true | 显示名 |
| Email | string | true | 邮箱 |
| Mobile | string | true | 手机号 |
| Source | string | true | 用户来源 |
| Status | i32 | true | 用户状态 |
| Icon | string | true | 用户头像 |
| Description | string | true | 用户描述 |
| RoleName | string | true | 角色名（TenantAdmin/TenantMember/TenantVisitor等） |
| Orgs | list[user.OrgRoleEntry] | false | 组织角色列表 |
| UserGroups | list[user.UserGroupEntry] | false | 用户组列表 |
| HasPassword | bool | true | 是否设置密码 |

### 5. user.OrgRoleEntry（组织角色条目）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| OrgID | string | true | 组织ID |
| RoleName | string | true | 组织角色名 |

### 6. user.UserGroupEntry（用户组条目）
| 参数 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| UserGroupID | string | true | 用户组ID |
| UserGroupName | string | true | 用户组名称 |

### 7. enums.IdentityType（身份类型）
接口关联枚举类型，用于标识成员/用户身份类型


# ListApp 接口文档
## 一、基础信息
- 所属服务：**AppService**
- 接口Action：**ListApp**
- 请求方法：**POST**
- 接口用途：智能体管理-获取用户端智能体列表

## 二、请求参数（app.ListAppRequest）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| ListOpt | common.ListOption | 否 | 分页与排序配置 |
| Filter | app.ListAppFilter | 否 | 智能体列表筛选条件 |
| Top | base.TopParam | 是 | TOP公共参数，前端无需处理 |

---
### 2.1 common.ListOption（分页排序通用结构）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| PageNumber | int32 | 否 | 页码，默认从 **1** 开始 |
| PageSize | int32 | 否 | 每页条数，默认遵循平台规范 |
| OrderBy | string | 否 | 排序字段 |
| Order | string | 否 | 排序方式：**ASC**(升序)/**DESC**(降序) |

### 2.2 app.ListAppFilter（智能体筛选条件）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| Keyword | string | 否 | 搜索关键词，匹配智能体名称/描述 |
| AppType | common.AppType | 否 | 智能体类型 |
| Status | int32 | 否 | 智能体状态 |
| CreateTimeStart | string | 否 | 创建时间起始，**RFC3339** 格式 |
| CreateTimeEnd | string | 否 | 创建时间结束，**RFC3339** 格式 |
| IsFavorite | bool | 否 | 是否仅查询收藏智能体 |
| WorkspaceID | string | 否 | 所属工作空间ID |

### 2.3 base.TopParam（TOP公共参数）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| UserID | string | 是 | 用户唯一标识 |
| RequestID | string | 否 | 请求唯一标识，用于链路追踪 |
| TenantID | string | 否 | 租户ID |
| Region | string | 否 | 地域标识 |

---
## 三、响应参数（app.ListAppResponse）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| Items | list[app.AppListItem] | 是 | 智能体列表数据 |
| Total | int32 | 是 | 符合条件的智能体总数量 |
| BaseResp | base.BaseResp | 否 | 公共响应基础信息 |

---
### 3.1 app.AppListItem（智能体列表项）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| AppID | string | 是 | 智能体唯一ID |
| Name | string | 是 | 智能体名称 |
| Description | string | 否 | 智能体描述 |
| Icon | string | 否 | 智能体图标 |
| Background | string | 否 | 图标背景色 |
| AppType | common.AppType | 是 | 智能体类型 |
| Status | int32 | 是 | 智能体状态 |
| CreateTime | string | 是 | 创建时间，**RFC3339** 格式 |
| UpdateTime | string | 是 | 更新时间，**RFC3339** 格式 |
| CreateUser | string | 是 | 创建人ID |
| WorkspaceID | string | 是 | 所属工作空间ID |
| IsFavorite | bool | 否 | 当前用户是否收藏 |
| PublishStatus | int32 | 否 | 发布状态 |

### 3.2 base.BaseResp（公共响应基础结构）
| 参数名 | 类型 | 是否必填 | 说明 |
| ------ | ---- | -------- | ---- |
| Code | int32 | 是 | 响应码，**0** 表示成功 |
| Message | string | 否 | 响应描述信息 |
| RequestID | string | 否 | 请求ID，与入参RequestID一致 |

### 3.3 common.AppType（智能体类型枚举）
| 枚举值 | 说明 |
| ------ | ---- |
| Single | 单Agent模式 |
| Multi | 多Agent模式 |
| ChatFlow | 对话流模式 |
| Workflow | 流程编排模式 |当前文件内容过长，豆包只阅读了前 51%。