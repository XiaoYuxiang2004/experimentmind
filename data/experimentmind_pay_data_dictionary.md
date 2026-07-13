# ExperimentMind Pay 用户级支付实验数据口径

## 1. 文档目的

本文档定义 ExperimentMind Pay V0.1 使用的数据表结构、字段含义、统计口径与数据质量约束。

本项目当前分析的场景是：

> 比较 A、B 两种收银台支付策略，判断新策略是否改善支付转化、支付收入和支付体验，同时检查退款等副作用。

---

## 2. 实验场景

- **A 组**：原有收银台支付策略。
- **B 组**：待评估的新收银台支付策略。
- **随机化单位**：用户。
- **分析单位**：用户。
- **分组原则**：同一用户在同一个实验中只能属于一个实验组。
- **实验干预**：用户进入符合条件的收银台后，系统展示其所属实验组对应的页面或支付策略。

A、B 两组用户都可能成功曝光：

- `group = A, exposed = 1`：用户看到了 A 版收银台。
- `group = B, exposed = 1`：用户看到了 B 版收银台。

---

## 3. 数据表定位

当前输入文件是：

> **用户级支付实验分析宽表**

数据粒度为：

```text
一行 = 一个用户在整个实验观察期内的汇总结果
```

它不是：

- 逐笔订单表；
- 原始支付流水表；
- 逐事件埋点日志；
- 一次曝光一行的事件长表。

即使一个用户在实验期间多次进入收银台、多次尝试支付或多次成功支付，也只保留一行，通过次数和金额字段进行汇总。

---

## 4. 实验曝光定义

当前项目中的“曝光”不是商品曝光，也不是广告曝光。

**支付实验曝光**定义为：

> 用户进入收银台后，系统成功展示了其所属实验组对应的支付页面或支付策略。

一个用户在实验期间可能发生多次曝光，因此同时保留：

- `exposed`：是否至少成功曝光过一次；
- `exposure_count`：实验期间成功曝光的总次数；
- `first_exposure_at`：第一次成功曝光的时间。

例如，一个 B 组用户在实验期间进入新版收银台 3 次：

```text
group = B
exposed = 1
exposure_count = 3
```

---

## 5. CSV 字段顺序

```csv
user_id,group,assigned_at,exposed,exposure_count,first_exposure_at,attempted,attempt_count,paid,payment_amount,refunded,refund_amount,payment_latency_ms,device,new_user
```

---

## 6. 字段总览

| 字段名 | 中文名称 | 推荐类型 | 是否允许为空 | 数据粒度 |
|---|---|---|---|---|
| `user_id` | 用户唯一标识 | string | 否 | 用户 |
| `group` | 实验分组 | category/string | 否 | 用户 |
| `assigned_at` | 实验分组时间 | datetime | 否 | 用户 |
| `exposed` | 是否成功曝光 | integer | 否 | 用户 |
| `exposure_count` | 曝光次数 | integer | 否 | 用户 |
| `first_exposure_at` | 首次曝光时间 | datetime | 条件允许 | 用户 |
| `attempted` | 是否发起过支付 | integer | 否 | 用户 |
| `attempt_count` | 支付尝试次数 | integer | 否 | 用户 |
| `paid` | 是否支付成功 | integer | 否 | 用户 |
| `payment_amount` | 成功支付总金额 | decimal | 否 | 用户 |
| `refunded` | 是否发生退款 | integer | 否 | 用户 |
| `refund_amount` | 退款总金额 | decimal | 否 | 用户 |
| `payment_latency_ms` | 首次成功支付耗时 | integer/float | 条件允许 | 用户 |
| `device` | 首次曝光设备类型 | category/string | 否 | 用户 |
| `new_user` | 是否为支付新用户 | integer | 否 | 用户 |

---

## 7. 字段详细口径

### 7.1 `user_id`

**含义：** 用户唯一标识。

**约束：**

- 不允许为空；
- 在同一个实验数据文件中必须唯一；
- 同一用户不得同时出现在 A、B 两组；
- 建议按字符串读取，避免前导零丢失；
- 不应使用姓名、手机号等直接身份信息。

---

### 7.2 `group`

**含义：** 用户被随机分配到的支付策略版本。

**允许值：**

```text
A
B
```

**约束：**

- 不允许为空；
- 数据文件中必须同时存在 A、B 两组；
- 同一用户的分组在整个实验期间保持不变。

---

### 7.3 `assigned_at`

**含义：** 用户被分配到实验组的时间。

**类型：** datetime。

**约束：**

- 不允许为空；
- 必须能够被解析为合法时间；
- 若用户成功曝光，应满足：

```text
assigned_at <= first_exposure_at
```

---

### 7.4 `exposed`

**含义：** 用户在实验观察期内是否至少成功看到过一次所属实验组的收银台策略。

**允许值：**

```text
1 = 至少成功曝光过一次
0 = 从未成功曝光
```

**约束：**

- 只能为 0 或 1；
- 不允许为空；
- 与 `exposure_count`、`first_exposure_at` 保持一致。

---

### 7.5 `exposure_count`

**含义：** 用户在实验观察期内成功看到实验收银台的总次数。

**类型：** 非负整数。

**约束：**

```text
exposed = 0  → exposure_count = 0
exposed = 1  → exposure_count >= 1
```

该字段可用于分析重复进入收银台、用户犹豫程度等行为，但不应把多次曝光当成多个独立用户。

---

### 7.6 `first_exposure_at`

**含义：** 用户第一次成功看到所属实验组收银台策略的时间。

**类型：** datetime。

**可空规则：**

```text
exposed = 0 → first_exposure_at 必须为空
exposed = 1 → first_exposure_at 必须有值
```

---

### 7.7 `attempted`

**含义：** 用户在实验观察期内是否至少正式发起过一次支付请求。

**允许值：**

```text
1 = 至少发起过一次支付
0 = 从未发起支付
```

**约束：**

- 只能为 0 或 1；
- 不允许为空；
- 当前实验限定所有支付尝试均从实验收银台发起，因此：

```text
attempted <= exposed
```

---

### 7.8 `attempt_count`

**含义：** 用户在实验观察期内正式发起支付请求的总次数。

**类型：** 非负整数。

**约束：**

```text
attempted = 0 → attempt_count = 0
attempted = 1 → attempt_count >= 1
```

支付失败后重新尝试，应计为新的支付尝试。

---

### 7.9 `paid`

**含义：** 用户在实验观察期内是否至少完成过一次成功支付。

**允许值：**

```text
1 = 至少成功支付过一次
0 = 从未支付成功
```

**约束：**

- 只能为 0 或 1；
- 不允许为空；
- 必须满足：

```text
paid <= attempted
```

---

### 7.10 `payment_amount`

**含义：** 用户在实验观察期内所有成功支付的实付金额总和。

**单位：** 当前默认人民币元。

**约束：**

- 不允许为空；
- 必须大于等于 0；
- 当前版本不纳入零元订单，因此：

```text
paid = 0 → payment_amount = 0
paid = 1 → payment_amount > 0
```

该字段表示退款前的成功支付总金额，退款金额单独记录在 `refund_amount` 中。

---

### 7.11 `refunded`

**含义：** 用户在退款观察窗口内是否至少发生过一次退款。

**允许值：**

```text
1 = 至少发生过一次退款
0 = 没有发生退款
```

**约束：**

- 只能为 0 或 1；
- 不允许为空；
- 原则上满足：

```text
refunded <= paid
```

退款观察窗口必须在整个实验中保持一致，例如“支付成功后 7 天内”。

---

### 7.12 `refund_amount`

**含义：** 用户在统一退款观察窗口内的累计退款金额。

**单位：** 当前默认人民币元。

**约束：**

- 不允许为空；
- 必须大于等于 0；
- 应满足：

```text
refunded = 0 → refund_amount = 0
refunded = 1 → refund_amount > 0
refund_amount <= payment_amount
```

---

### 7.13 `payment_latency_ms`

**含义：** 用户首次成功支付对应的支付请求，从正式发起到返回成功结果所经历的时间。

**单位：** 毫秒。

**可空规则：**

```text
paid = 0 → payment_latency_ms 必须为空
paid = 1 → payment_latency_ms 必须大于 0
```

不应使用 0 表示“没有支付成功”，因为 0 会被误计入平均支付耗时。

计算平均支付耗时时，只对 `paid = 1` 且该字段非空的用户求均值。

---

### 7.14 `device`

**含义：** 用户首次成功曝光实验收银台时所使用的设备或客户端类型。

**推荐值：**

```text
ios
android
web
mini_program
other
```

**约束：**

- 不允许为空；
- 推荐全部使用小写；
- 同义值必须统一，例如不能同时出现 `iOS`、`IOS` 和 `ios`。

若用户未成功曝光，可记录分组时的设备类型；项目文档中必须保持口径一致。

---

### 7.15 `new_user`

**含义：** 用户在 `assigned_at` 时点之前是否没有历史成功支付记录。

**允许值：**

```text
1 = 支付新用户
0 = 支付老用户
```

**约束：**

- 只能为 0 或 1；
- 不允许为空；
- 用户类型必须使用实验开始前的信息确定，不能根据实验期间的支付结果修改。

---

## 8. 跨字段业务规则

数据进入指标计算前，应至少满足以下关系。

### 8.1 支付漏斗关系

```text
paid <= attempted <= exposed
```

### 8.2 曝光次数关系

```text
exposed = 0 → exposure_count = 0
exposed = 1 → exposure_count >= 1
```

### 8.3 首次曝光时间关系

```text
exposed = 0 → first_exposure_at 为空
exposed = 1 → first_exposure_at 非空
assigned_at <= first_exposure_at
```

### 8.4 支付尝试次数关系

```text
attempted = 0 → attempt_count = 0
attempted = 1 → attempt_count >= 1
```

### 8.5 支付金额关系

```text
paid = 0 → payment_amount = 0
paid = 1 → payment_amount > 0
```

### 8.6 支付耗时关系

```text
paid = 0 → payment_latency_ms 为空
paid = 1 → payment_latency_ms > 0
```

### 8.7 退款关系

```text
refunded <= paid
refunded = 0 → refund_amount = 0
refunded = 1 → refund_amount > 0
refund_amount <= payment_amount
```

---

## 9. 当前数据可以计算的指标

### 9.1 实验诊断指标

#### 分组用户数

```text
COUNT(user_id)
```

#### 收银台曝光率

```text
曝光用户数 / 分组用户数
```

#### 人均曝光次数

```text
曝光总次数 / 曝光用户数
```

---

### 9.2 核心指标

#### 曝光后最终支付转化率

```text
支付成功用户数 / 曝光用户数
```

这是当前 V0.1 的核心业务指标。

---

### 9.3 支付漏斗指标

#### 支付发起率

```text
发起支付用户数 / 曝光用户数
```

#### 尝试后支付成功率

```text
支付成功用户数 / 发起支付用户数
```

#### 人均支付尝试次数

```text
支付尝试总次数 / 发起支付用户数
```

---

### 9.4 收入指标

#### 每曝光用户支付收入

```text
支付金额总和 / 曝光用户数
```

#### 支付用户平均支付金额

```text
支付金额总和 / 支付成功用户数
```

#### 每曝光用户净收入

```text
(支付金额总和 - 退款金额总和) / 曝光用户数
```

---

### 9.5 护栏指标

#### 退款用户率

```text
退款用户数 / 支付成功用户数
```

#### 平均首次成功支付耗时

```text
MEAN(payment_latency_ms)
```

只在 `paid = 1` 且 `payment_latency_ms` 非空的用户中计算。

---

## 10. A/B 比较原则

系统分别为 A、B 两组计算同一指标，然后输出：

- A 组指标值；
- B 组指标值；
- 绝对差值；
- 相对提升；
- 置信区间；
- P 值；
- 是否达到统计显著；
- 是否具有业务意义。

例如：

```text
A 组最终支付转化率 = A 组支付成功用户数 / A 组曝光用户数
B 组最终支付转化率 = B 组支付成功用户数 / B 组曝光用户数
```

绝对提升：

```text
B 组转化率 - A 组转化率
```

相对提升：

```text
(B 组转化率 - A 组转化率) / A 组转化率
```

---

## 11. CSV 示例

```csv
user_id,group,assigned_at,exposed,exposure_count,first_exposure_at,attempted,attempt_count,paid,payment_amount,refunded,refund_amount,payment_latency_ms,device,new_user
U001,A,2026-07-13 09:00:00,1,1,2026-07-13 09:02:00,1,1,1,128.50,0,0,1350,ios,1
U002,A,2026-07-13 09:05:00,1,2,2026-07-13 09:06:00,0,0,0,0,0,0,,android,0
U003,A,2026-07-13 09:10:00,1,3,2026-07-13 09:12:00,1,2,0,0,0,0,,ios,1
U004,B,2026-07-13 09:15:00,1,1,2026-07-13 09:16:00,1,1,1,256.00,0,0,980,android,0
U005,B,2026-07-13 09:20:00,1,2,2026-07-13 09:21:00,1,1,1,168.00,1,168.00,1100,ios,1
U006,B,2026-07-13 09:25:00,0,0,,0,0,0,0,0,0,,android,0
```

---

## 12. 当前版本的数据边界

V0.1 暂不支持：

- 一行一笔订单的订单粒度输入；
- 一行一次事件的埋点长表；
- 多张原始表自动关联；
- 订单级支付成功率；
- 支付失败原因分布；
- 多次退款明细；
- 每次曝光和每次支付尝试的时间序列。

后续版本可将原始实验用户表、事件表和订单表聚合为本文定义的用户级宽表，再进入同一套指标与统计分析流程。
