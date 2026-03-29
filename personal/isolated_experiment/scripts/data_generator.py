#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据生成脚本 - 为每次实验运行生成独立的数据副本
确保每次运行数据分布一致但内容不同，排除上下文干扰
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import json

class DataGenerator:
    """数据生成器类，为每次实验运行生成独立数据"""
    
    def __init__(self, run_id, base_seed=42):
        """
        初始化数据生成器
        
        Args:
            run_id: 运行ID，用于生成唯一数据
            base_seed: 基础随机种子
        """
        self.run_id = run_id
        self.seed = base_seed + run_id * 1000  # 确保每次运行种子不同
        np.random.seed(self.seed)
        
        # 基础统计特性（固定）
        self.base_stats = {
            'age': {'mean': 35, 'std': 8},
            'income': {'mean': 70000, 'std': 20000},
            'spending_score': {'mean': 80, 'std': 12},
            'sales': {'mean': 2000, 'std': 600}
        }
        
    def generate_task1_data(self, n_samples=50):
        """
        生成Task 1数据：age, income, spending_score
        
        Args:
            n_samples: 样本数量
            
        Returns:
            DataFrame: 生成的数据
        """
        print(f'[Run {self.run_id}] 生成Task 1数据...')
        
        # 基于固定统计特性生成数据
        age = np.random.normal(
            self.base_stats['age']['mean'],
            self.base_stats['age']['std'],
            n_samples
        ).astype(int)
        
        income = np.random.normal(
            self.base_stats['income']['mean'],
            self.base_stats['income']['std'],
            n_samples
        ).astype(int)
        
        spending_score = np.random.normal(
            self.base_stats['spending_score']['mean'],
            self.base_stats['spending_score']['std'],
            n_samples
        ).clip(0, 100).astype(int)  # 限制在0-100范围内
        
        # 创建DataFrame
        df = pd.DataFrame({
            'id': range(1, n_samples + 1),
            'age': age,
            'income': income,
            'spending_score': spending_score
        })
        
        # 验证统计特性
        print(f'  年龄统计: 均值={df["age"].mean():.1f}, 标准差={df["age"].std():.1f}')
        print(f'  收入统计: 均值={df["income"].mean():.1f}, 标准差={df["income"].std():.1f}')
        print(f'  消费评分: 均值={df["spending_score"].mean():.1f}, 标准差={df["spending_score"].std():.1f}')
        
        return df
    
    def generate_task2_data(self, n_samples=50):
        """
        生成Task 2数据：date, sales（包含缺失值和异常值）
        
        Args:
            n_samples: 样本数量
            
        Returns:
            DataFrame: 生成的数据
        """
        print(f'[Run {self.run_id}] 生成Task 2数据...')
        
        # 生成日期（过去365天内随机）
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=np.random.randint(0, 365)) 
                for _ in range(n_samples)]
        
        # 生成sales数据（基于固定统计特性）
        sales = np.random.normal(
            self.base_stats['sales']['mean'],
            self.base_stats['sales']['std'],
            n_samples
        )
        
        # 添加5%的缺失值
        missing_mask = np.random.random(n_samples) < 0.05
        sales[missing_mask] = np.nan
        
        # 添加5%的异常值（超出均值±2标准差）
        lower_bound = self.base_stats['sales']['mean'] - 2 * self.base_stats['sales']['std']
        upper_bound = self.base_stats['sales']['mean'] + 2 * self.base_stats['sales']['std']
        
        # 确保异常值确实超出范围
        outlier_mask = np.random.random(n_samples) < 0.05
        for i in range(n_samples):
            if outlier_mask[i] and not missing_mask[i]:
                # 随机决定是过高还是过低异常值
                if np.random.random() < 0.5:
                    sales[i] = lower_bound - np.random.uniform(100, 500)  # 过低异常值
                else:
                    sales[i] = upper_bound + np.random.uniform(100, 500)  # 过高异常值
        
        # 创建DataFrame
        df = pd.DataFrame({
            'id': range(1, n_samples + 1),
            'date': [d.strftime('%Y-%m-%d') for d in dates],
            'sales': sales
        })
        
        # 验证数据特性
        valid_sales = df['sales'].dropna()
        print(f'  有效sales数据: {len(valid_sales)}/{n_samples}行')
        print(f'  缺失值比例: {missing_mask.sum()}/{n_samples} ({missing_mask.sum()/n_samples*100:.1f}%)')
        print(f'  异常值比例: {outlier_mask.sum()}/{n_samples} ({outlier_mask.sum()/n_samples*100:.1f}%)')
        
        return df
    
    def generate_task4_data(self, n_samples=30):
        """
        生成Task 4测试数据：age, income
        
        Args:
            n_samples: 样本数量
            
        Returns:
            DataFrame: 生成的数据
        """
        print(f'[Run {self.run_id}] 生成Task 4数据...')
        
        # 生成年龄和收入数据
        age = np.random.normal(35, 10, n_samples).astype(int).clip(18, 70)
        income = np.random.normal(60000, 15000, n_samples)
        
        # 添加一些缺失值（用于测试忽略缺失值偏好）
        missing_mask = np.random.random(n_samples) < 0.1
        income = income.astype(float)  # 确保是浮点数类型
        income[missing_mask] = np.nan
        
        df = pd.DataFrame({
            'id': range(1, n_samples + 1),
            'age': age,
            'income': income
        })
        
        print(f'  数据统计: {n_samples}行，{missing_mask.sum()}个缺失值')
        
        return df
    
    def save_data(self, df, task_name, data_dir):
        """
        保存数据到文件
        
        Args:
            df: DataFrame数据
            task_name: 任务名称
            data_dir: 数据目录
        """
        filename = f'{task_name}_run{self.run_id}.csv'
        filepath = os.path.join(data_dir, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f'  数据保存到: {filepath}')
        
        return filepath

def main():
    """主函数：生成所有任务的数据"""
    import sys
    
    if len(sys.argv) < 2:
        print('用法: python data_generator.py <run_id>')
        sys.exit(1)
    
    run_id = int(sys.argv[1])
    
    # 创建数据生成器
    generator = DataGenerator(run_id)
    
    # 设置数据目录
    base_dir = r'D:\collections2026\phd_application\nanobot1\personal\isolated_experiment'
    data_dir = os.path.join(base_dir, 'data')
    
    # 生成并保存Task 1数据
    print(f'\n=== 生成Run {run_id}的数据 ===')
    
    # Task 1数据
    task1_df = generator.generate_task1_data(50)
    task1_path = generator.save_data(task1_df, 'task1', data_dir)
    
    # Task 2数据
    task2_df = generator.generate_task2_data(50)
    task2_path = generator.save_data(task2_df, 'task2', data_dir)
    
    # Task 4数据
    task4_df = generator.generate_task4_data(30)
    task4_path = generator.save_data(task4_df, 'task4', data_dir)
    
    # 保存数据信息
    info = {
        'run_id': run_id,
        'seed': generator.seed,
        'data_files': {
            'task1': task1_path,
            'task2': task2_path,
            'task4': task4_path
        },
        'base_stats': generator.base_stats,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    info_path = os.path.join(data_dir, f'run{run_id}_info.json')
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f'\n数据信息保存到: {info_path}')
    print(f'=== Run {run_id} 数据生成完成 ===')

if __name__ == '__main__':
    main()