# NanoClaw - 轻量级 Agent 运行时

一个极简的 Python Agent 运行时，专为与 genesis-cloud-sim 集成设计。

## 特性

- **极简核心** - 仅 ~500 行代码，零外部依赖
- **技能系统** - 将任何函数封装为可复用的 Skill
- **上下文管理** - 自动状态追踪和历史记录
- **事件驱动** - 支持事件订阅和处理
- **任务链** - 顺序/并行执行多个技能
- **Genesis 集成** - 一键集成 genesis-cloud-sim

## 快速开始

### 基础用法

```python
from nanoclaw import NanoClaw

# 创建 Agent
agent = NanoClaw("my_agent")

# 注册技能
@agent.skill("greet", description="打招呼")
def greet(context, name: str = "World"):
    return f"Hello, {name}!"

# 调用技能
result = agent.call("greet", name="Alice")
print(result['result'])  # "Hello, Alice!"
```

### 与 Genesis 集成

```python
from nanoclaw import NanoClaw, GenesisIntegration, SimConfig

# 创建 Agent
agent = NanoClaw("robot_agent")

# 集成 Genesis
integration = GenesisIntegration(agent)
integration.setup(SimConfig(
    task_id="pick_object",
    headless=True,
    record=True
))

# 重置仿真环境
result = agent.call("sim.reset", task_id="pick_object", seed=42)

# 运行 episode
result = agent.call("sim.run_episode", max_steps=100)
print(f"Completed {result['result']['steps']} steps")

# 关闭
integration.close()
```

### 自定义技能链

```python
# 注册感知技能
@agent.skill("perceive.objects")
def perceive_objects(context):
    # 调用检测模型
    objects = detect_objects()
    context.set('objects', objects)
    return objects

# 注册规划技能
@agent.skill("plan.grasp")
def plan_grasp(context, object_id: str):
    objects = context.get('objects', [])
    target = find_object(objects, object_id)
    plan = generate_grasp_plan(target)
    context.set('plan', plan)
    return plan

# 注册执行技能
@agent.skill("execute.plan")
def execute_plan(context):
    plan = context.get('plan')
    for step in plan:
        agent.call("sim.step", action=step)
    return "done"

# 执行任务链
results = agent.chain(
    {'skill': 'perceive.objects'},
    {'skill': 'plan.grasp', 'args': {'object_id': 'cup'}},
    {'skill': 'execute.plan'}
)
```

### Agent 思考过程

```python
# Agent 记录思考过程
agent.think("我需要先检测物体")

# 记忆信息
agent.remember('goal', 'pick_up_cup')

# 回忆信息
goal = agent.recall('goal')

# 查看完整上下文
info = agent.info()
```

## 与 genesis-cloud-sim 深度集成

### 可用的仿真技能

集成后，Agent 可以使用以下技能：

| 技能 | 描述 |
|------|------|
| `sim.reset` | 重置仿真环境 |
| `sim.step` | 执行仿真步 |
| `sim.get_obs` | 获取观测 |
| `sim.render` | 渲染画面 |
| `sim.close` | 关闭仿真 |
| `sim.run_episode` | 运行完整 episode |
| `sim.evaluate_policy` | 评测策略 |
| `sim.collect_data` | 收集训练数据 |

### 高级用法

```python
from nanoclaw import create_genesis_agent

# 一键创建带 Genesis 集成的 Agent
agent = create_genesis_agent(
    name="my_robot",
    sim_config=SimConfig(
        task_id="pick_and_place",
        headless=False
    )
)

# 定义策略函数
def my_policy(observation):
    # 你的策略逻辑
    return {'joint_positions': [0.1, -0.2, 0.3, ...]}

# 使用策略运行 episode
result = agent.call("sim.run_episode", 
                   policy=my_policy, 
                   max_steps=200)

# 收集训练数据
result = agent.call("sim.collect_data",
                   policy=my_policy,
                   num_episodes=100,
                   save_path="./data/training.pkl")

# 评测策略
result = agent.call("sim.evaluate_policy",
                   policy=my_policy,
                   num_episodes=50)
print(f"Success rate: {result['result']['success_rate']:.2%}")
```

## 运行示例

```bash
cd genesis-cloud-sim
python nanoclaw/example.py
```

## API 参考

### NanoClaw

```python
agent = NanoClaw(name="my_agent")

# 技能管理
agent.skill(name, description)(func)  # 装饰器注册
agent.register_skill(skill)            # 直接注册
agent.get_skill(name)                  # 获取技能
agent.list_skills()                    # 列出技能

# 技能调用
agent.call(skill_name, **kwargs)       # 调用单个技能
agent.chain(*calls)                    # 顺序执行链
agent.parallel(*calls)                 # 并行执行

# 状态管理
agent.remember(key, value)             # 记忆
agent.recall(key, default)             # 回忆
agent.think(message)                   # 思考记录

# 事件
agent.on(event_type, handler)          # 订阅事件

# 信息
agent.info()                           # 获取完整信息
agent.export_session(filepath)         # 导出会话
agent.reset()                          # 重置
```

### GenesisIntegration

```python
integration = GenesisIntegration(agent)

# 设置
integration.setup(sim_config, genesis_config)

# 为特定任务创建环境技能
env_skill = integration.create_env_skill("pick_object", seed=42)
agent.register_skill(env_skill)

# 关闭
integration.close()
```

## 架构

```
NanoClaw Agent
├── Core (核心运行时)
│   ├── Skill Registry (技能注册表)
│   ├── Context (上下文管理)
│   ├── Event Bus (事件总线)
│   └── Task Chain (任务链)
│
├── Integration (集成层)
│   └── GenesisIntegration (Genesis 集成)
│       ├── SimNode wrapper
│       ├── Composite skills
│       └── Environment factory
│
└── Skills (技能层)
    ├── Built-in sim skills
    ├── User-defined skills
    └── Composite skills
```

## 与 OpenClaw 的关系

NanoClaw 是一个**极简、自包含**的 Agent 运行时，可以作为：

1. **独立使用** - 小型项目的完整 Agent 解决方案
2. ** genesis-cloud-sim 的 Agent 层** - 直接控制仿真
3. **大型 Agent 平台的组件** - 作为 Skill 执行引擎

如果你想连接到更大的 Agent 生态（如 AutoGPT、LangChain），只需将 NanoClaw 包装为 Skill 注册到这些平台。

## 依赖

- Python >= 3.8
- 标准库 only (logging, typing, dataclasses, etc.)
- genesis-cloud-sim (可选，用于仿真集成)

## 许可证

Apache 2.0
