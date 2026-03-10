"""
NanoClaw + Genesis 集成

让 NanoClaw Agent 可以控制 genesis-cloud-sim 仿真环境
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from .core import NanoClaw, Skill, Context

# 尝试导入 genesis-cloud-sim 组件
try:
    from runtime import SimNode, SimNodeConfig
    from runtime.replay_engine import FrameType
    GENESIS_AVAILABLE = True
except ImportError:
    GENESIS_AVAILABLE = False
    logging.warning("Genesis runtime not available, integration will be limited")

logger = logging.getLogger("nanoclaw.integration")


@dataclass
class SimConfig:
    """仿真配置"""
    task_id: str = "default_task"
    seed: int = 0
    headless: bool = True
    record: bool = True
    max_steps: int = 1000


class SimSkill:
    """
    仿真技能包装器
    
    将 Genesis SimNode 包装为 NanoClaw Skill
    """
    
    def __init__(self, sim_node: Optional[Any] = None, config: Optional[SimConfig] = None):
        self.sim = sim_node
        self.config = config or SimConfig()
        self.is_initialized = False
        self.current_obs = None
        self.step_count = 0
    
    def reset(self, context: Context, **kwargs) -> Dict:
        """重置仿真环境"""
        if not GENESIS_AVAILABLE or self.sim is None:
            return {'success': False, 'error': 'Genesis not available'}
        
        task_id = kwargs.get('task_id', self.config.task_id)
        seed = kwargs.get('seed', self.config.seed)
        
        try:
            obs = self.sim.reset(task_id, seed)
            self.current_obs = obs
            self.step_count = 0
            self.is_initialized = True
            
            # 保存到上下文
            context.set('sim_task_id', task_id)
            context.set('sim_seed', seed)
            
            return {
                'success': True,
                'observation': self._obs_to_dict(obs),
                'task_id': task_id,
                'seed': seed
            }
        
        except Exception as e:
            logger.error(f"Sim reset failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def step(self, context: Context, **kwargs) -> Dict:
        """执行一步"""
        if not self.is_initialized:
            return {'success': False, 'error': 'Sim not initialized, call reset first'}
        
        action = kwargs.get('action', {})
        
        try:
            obs, reward, done, info = self.sim.step(action)
            self.current_obs = obs
            self.step_count += 1
            
            # 更新上下文
            context.set('sim_step', self.step_count)
            context.set('sim_reward', context.get('sim_reward', 0) + reward)
            
            return {
                'success': True,
                'observation': self._obs_to_dict(obs),
                'reward': reward,
                'done': done,
                'info': info,
                'step': self.step_count
            }
        
        except Exception as e:
            logger.error(f"Sim step failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_obs(self, context: Context, **kwargs) -> Dict:
        """获取当前观测"""
        if self.current_obs is None:
            return {'success': False, 'error': 'No observation available'}
        
        return {
            'success': True,
            'observation': self._obs_to_dict(self.current_obs)
        }
    
    def render(self, context: Context, **kwargs) -> Dict:
        """渲染当前帧"""
        if self.sim is None:
            return {'success': False, 'error': 'Sim not available'}
        
        try:
            image = self.sim.render()
            return {
                'success': True,
                'image': image
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def close(self, context: Context, **kwargs) -> Dict:
        """关闭仿真"""
        if self.sim:
            try:
                self.sim.close()
                return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': True}
    
    def _obs_to_dict(self, obs) -> Dict:
        """转换观测为字典"""
        if hasattr(obs, 'to_dict'):
            return obs.to_dict()
        elif hasattr(obs, '__dict__'):
            return obs.__dict__
        else:
            return {'data': str(obs)}
    
    def to_skills(self) -> List[Skill]:
        """转换为技能列表"""
        return [
            Skill(name="sim.reset", description="重置仿真环境", func=self.reset),
            Skill(name="sim.step", description="执行仿真步", func=self.step),
            Skill(name="sim.get_obs", description="获取观测", func=self.get_obs),
            Skill(name="sim.render", description="渲染画面", func=self.render),
            Skill(name="sim.close", description="关闭仿真", func=self.close),
        ]


class GenesisIntegration:
    """
    NanoClaw + Genesis 集成器
    
    一键集成 genesis-cloud-sim 到 NanoClaw Agent
    """
    
    def __init__(self, agent: NanoClaw):
        self.agent = agent
        self.sim_skill: Optional[SimSkill] = None
        self.sim_node: Optional[Any] = None
    
    def setup(self, sim_config: Optional[SimConfig] = None, 
              genesis_config: Optional[Dict] = None) -> 'GenesisIntegration':
        """
        设置集成
        
        Args:
            sim_config: 仿真配置
            genesis_config: Genesis 引擎配置
        """
        if not GENESIS_AVAILABLE:
            logger.error("Cannot setup: Genesis runtime not available")
            return self
        
        sim_config = sim_config or SimConfig()
        
        # 创建 Sim Node
        node_config = SimNodeConfig(
            headless=sim_config.headless,
            record_trajectory=sim_config.record
        )
        
        self.sim_node = SimNode(node_config)
        self.sim_skill = SimSkill(self.sim_node, sim_config)
        
        # 注册所有仿真技能
        for skill in self.sim_skill.to_skills():
            self.agent.register_skill(skill)
        
        # 注册高级复合技能
        self._register_composite_skills()
        
        logger.info("Genesis integration setup complete")
        return self
    
    def _register_composite_skills(self):
        """注册复合技能"""
        
        @self.agent.skill("sim.run_episode", description="运行完整 episode")
        def run_episode(context: Context, max_steps: int = 1000, policy=None, **kwargs):
            """运行完整 episode"""
            # 重置
            reset_result = self.agent.call("sim.reset", **kwargs)
            if not reset_result['success']:
                return reset_result
            
            observations = []
            actions = []
            rewards = []
            
            for step in range(max_steps):
                # 获取观测
                if policy is None:
                    # 随机策略
                    import random
                    action = {'joint_positions': [random.uniform(-1, 1) for _ in range(7)]}
                else:
                    obs = self.agent.call("sim.get_obs")['result']['observation']
                    action = policy(obs)
                
                # 执行步
                step_result = self.agent.call("sim.step", action=action)
                if not step_result['success']:
                    break
                
                observations.append(step_result['result']['observation'])
                actions.append(action)
                rewards.append(step_result['result']['reward'])
                
                if step_result['result']['done']:
                    break
            
            return {
                'success': True,
                'steps': len(rewards),
                'total_reward': sum(rewards),
                'observations': observations,
                'actions': actions
            }
        
        @self.agent.skill("sim.evaluate_policy", description="评测策略")
        def evaluate_policy(context: Context, policy, num_episodes: int = 10, **kwargs):
            """评测策略"""
            results = []
            
            for ep in range(num_episodes):
                episode_result = self.agent.call("sim.run_episode", 
                                                policy=policy, 
                                                seed=ep,
                                                **kwargs)
                results.append(episode_result)
            
            successes = sum(1 for r in results if r.get('success'))
            avg_reward = sum(r['result']['total_reward'] for r in results if r['success']) / max(successes, 1)
            
            return {
                'success': True,
                'episodes': num_episodes,
                'success_rate': successes / num_episodes,
                'avg_reward': avg_reward,
                'results': results
            }
        
        @self.agent.skill("sim.collect_data", description="收集训练数据")
        def collect_data(context: Context, 
                        num_episodes: int = 100,
                        policy=None,
                        save_path: str = "./data/collected.pkl",
                        **kwargs):
            """收集训练数据"""
            import pickle
            import os
            
            all_data = []
            
            for ep in range(num_episodes):
                result = self.agent.call("sim.run_episode", 
                                        policy=policy,
                                        seed=ep,
                                        **kwargs)
                
                if result['success']:
                    all_data.append({
                        'episode': ep,
                        'observations': result['result']['observations'],
                        'actions': result['result']['actions'],
                        'total_reward': result['result']['total_reward']
                    })
                
                if (ep + 1) % 10 == 0:
                    logger.info(f"Collected {ep + 1}/{num_episodes} episodes")
            
            # 保存
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                pickle.dump(all_data, f)
            
            return {
                'success': True,
                'episodes_collected': len(all_data),
                'save_path': save_path
            }
    
    def create_env_skill(self, task_id: str, seed: int = 0) -> Skill:
        """
        为特定任务创建环境技能
        
        返回一个 Skill，封装特定任务的仿真环境
        """
        def env_skill(context: Context, action=None, reset=False, **kwargs):
            if reset or context.get('env_initialized') is None:
                result = self.agent.call("sim.reset", task_id=task_id, seed=seed)
                context.set('env_initialized', True)
                context.set('current_task', task_id)
                if action is None:
                    return result
            
            if action is not None:
                return self.agent.call("sim.step", action=action)
            
            return self.agent.call("sim.get_obs")
        
        return Skill(
            name=f"env.{task_id}",
            description=f"Environment for task {task_id}",
            func=env_skill
        )
    
    def close(self):
        """关闭集成"""
        if self.sim_node:
            self.sim_node.close()
            logger.info("Genesis integration closed")


# 便捷函数

def create_genesis_agent(name: str = "genesis_agent", 
                        sim_config: Optional[SimConfig] = None) -> Optional[NanoClaw]:
    """
    一键创建带有 Genesis 集成的 NanoClaw Agent
    
    Usage:
        agent = create_genesis_agent()
        
        # 重置环境
        result = agent.call("sim.reset", task_id="pick_object", seed=42)
        
        # 运行 episode
        result = agent.call("sim.run_episode", max_steps=100)
    """
    if not GENESIS_AVAILABLE:
        logger.error("Genesis runtime not available")
        return None
    
    agent = NanoClaw(name)
    integration = GenesisIntegration(agent)
    integration.setup(sim_config)
    
    return agent
