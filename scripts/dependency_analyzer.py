#!/usr/bin/env python3
"""
模块依赖分析工具

功能:
- 扫描所有 Python 文件
- 解析 import 语句
- 构建依赖关系图
- 识别循环依赖
- 识别孤立模块
- 识别过度依赖模块
- 生成 Graphviz DOT 格式
- 生成 HTML 交互式图表
- 提供重构建议

使用:
    python scripts/dependency_analyzer.py [--output-dir docs/architecture]
"""

import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class ModuleNode:
    """模块节点"""
    name: str
    path: str
    imports: Set[str] = field(default_factory=set)  # 导入的其他模块
    imported_by: Set[str] = field(default_factory=set)  # 被哪些模块导入
    layer: str = "unknown"  # 层级：core, feature, app


@dataclass
class DependencyGraph:
    """依赖关系图"""
    modules: Dict[str, ModuleNode] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)
    
    def add_module(self, name: str, path: str) -> ModuleNode:
        """添加模块"""
        if name not in self.modules:
            self.modules[name] = ModuleNode(name=name, path=path)
        return self.modules[name]
    
    def add_dependency(self, from_module: str, to_module: str):
        """添加依赖关系"""
        if from_module in self.modules and to_module in self.modules:
            self.modules[from_module].imports.add(to_module)
            self.modules[to_module].imported_by.add(from_module)
    
    def find_cycles(self) -> List[List[str]]:
        """查找循环依赖 (使用 DFS)"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in self.modules:
                for neighbor in self.modules[node].imports:
                    if neighbor not in visited:
                        cycle = dfs(neighbor)
                        if cycle:
                            return cycle
                    elif neighbor in rec_stack:
                        # 找到循环
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)
                        return cycle
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        for module in self.modules:
            if module not in visited:
                dfs(module)
        
        self.cycles = cycles
        return cycles
    
    def find_isolated_modules(self) -> List[str]:
        """查找孤立模块 (既没有导入也没有被导入)"""
        isolated = []
        for name, module in self.modules.items():
            if not module.imports and not module.imported_by:
                isolated.append(name)
        return isolated
    
    def find_over_dependent_modules(self, threshold: int = 5) -> List[Tuple[str, int]]:
        """查找过度依赖的模块 (导入过多其他模块)"""
        over_dependent = []
        for name, module in self.modules.items():
            if len(module.imports) > threshold:
                over_dependent.append((name, len(module.imports)))
        return sorted(over_dependent, key=lambda x: x[1], reverse=True)
    
    def find_heavily_depended_modules(self, threshold: int = 5) -> List[Tuple[str, int]]:
        """查找被过度依赖的模块 (被过多其他模块导入)"""
        heavily_depended = []
        for name, module in self.modules.items():
            if len(module.imported_by) > threshold:
                heavily_depended.append((name, len(module.imported_by)))
        return sorted(heavily_depended, key=lambda x: x[1], reverse=True)


class DependencyAnalyzer:
    """依赖分析器"""
    
    def __init__(self, root_path: str, exclude_patterns: List[str] = None):
        self.root_path = Path(root_path)
        self.exclude_patterns = exclude_patterns or [
            'venv', '__pycache__', 'migrations', 'node_modules', 
            '.git', '.venv', 'tests', 'test_*'
        ]
        self.graph = DependencyGraph()
        self.module_layers = {
            'config': 'core',
            'common': 'core',
            'users': 'core',
            'authentication': 'core',
            'websocket': 'core',
            'games': 'feature',
            'ai_engine': 'feature',
            'matchmaking': 'feature',
            'puzzles': 'feature',
            'daily_challenge': 'feature',
            'health': 'app',
        }
    
    def should_exclude(self, path: Path) -> bool:
        """检查路径是否应该排除"""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def get_module_name(self, file_path: Path) -> str:
        """从文件路径获取模块名"""
        try:
            rel_path = file_path.relative_to(self.root_path)
            parts = list(rel_path.parts)
            
            # 移除 .py 扩展名
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            
            # 处理 __init__.py
            if parts[-1] == '__init__':
                parts = parts[:-1]
            
            return '.'.join(parts) if parts else ''
        except ValueError:
            return file_path.stem
    
    def parse_imports(self, file_path: Path) -> Set[str]:
        """解析 Python 文件中的 import 语句"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        # 只添加项目内部模块
                        if module_name in self.module_layers or module_name == 'websocket':
                            imports.add(module_name)
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"⚠️  解析失败 {file_path}: {e}")
        
        return imports
    
    def scan_modules(self):
        """扫描所有 Python 模块"""
        print(f"🔍 扫描模块：{self.root_path}")
        
        for py_file in self.root_path.rglob('*.py'):
            if self.should_exclude(py_file):
                continue
            
            module_name = self.get_module_name(py_file)
            if not module_name:
                continue
            
            # 确定模块层级
            layer = 'unknown'
            for prefix, layer_name in self.module_layers.items():
                if module_name.startswith(prefix) or prefix in module_name:
                    layer = layer_name
                    break
            
            module = self.graph.add_module(module_name, str(py_file))
            module.layer = layer
            module.imports = self.parse_imports(py_file)
        
        # 建立依赖关系
        self._build_dependencies()
        
        print(f"✓ 找到 {len(self.graph.modules)} 个模块")
    
    def _build_dependencies(self):
        """构建模块间依赖关系"""
        module_names = set(self.graph.modules.keys())
        
        for module_name, module in self.graph.modules.items():
            # 复制 imports 集合避免迭代时修改
            imports_copy = list(module.imports)
            for imp in imports_copy:
                # 查找匹配的模块
                for target_name in module_names:
                    if target_name == imp or target_name.endswith(f'.{imp}'):
                        self.graph.add_dependency(module_name, target_name)
    
    def analyze(self) -> Dict:
        """执行完整分析"""
        self.scan_modules()
        
        # 查找循环依赖
        cycles = self.graph.find_cycles()
        
        # 查找孤立模块
        isolated = self.graph.find_isolated_modules()
        
        # 查找过度依赖模块
        over_dependent = self.graph.find_over_dependent_modules(threshold=3)
        
        # 查找被过度依赖模块
        heavily_depended = self.graph.find_heavily_depended_modules(threshold=3)
        
        return {
            'total_modules': len(self.graph.modules),
            'cycles': cycles,
            'isolated_modules': isolated,
            'over_dependent_modules': over_dependent,
            'heavily_depended_modules': heavily_depended,
        }
    
    def generate_dot(self, output_path: str):
        """生成 Graphviz DOT 格式"""
        colors = {
            'core': '#4CAF50',      # 绿色 - 核心层
            'feature': '#2196F3',   # 蓝色 - 功能层
            'app': '#FF9800',       # 橙色 - 应用层
            'unknown': '#9E9E9E',   # 灰色 - 未知
        }
        
        dot_lines = [
            'digraph ModuleDependencies {',
            '    rankdir=TB;',
            '    node [shape=box, style=filled, fontname="Arial"];',
            '    edge [fontname="Arial", fontsize=10];',
            '',
            '    // 图例',
            '    subgraph cluster_legend {',
            '        label="图例";',
            '        style=dashed;',
            '        legend_core [label="核心层", fillcolor="#4CAF50"];',
            '        legend_feature [label="功能层", fillcolor="#2196F3"];',
            '        legend_app [label="应用层", fillcolor="#FF9800"];',
            '    }',
            '',
        ]
        
        # 添加节点
        for name, module in self.graph.modules.items():
            color = colors.get(module.layer, colors['unknown'])
            label = name.split('.')[-1]  # 只显示最后一段
            dot_lines.append(f'    "{name}" [label="{label}", fillcolor="{color}"];')
        
        dot_lines.append('')
        
        # 添加边
        for name, module in self.graph.modules.items():
            for target in module.imports:
                if target in self.graph.modules:
                    dot_lines.append(f'    "{name}" -> "{target}";')
        
        # 标记循环依赖
        if self.graph.cycles:
            dot_lines.append('')
            dot_lines.append('    // 循环依赖 (红色)')
            for cycle in self.graph.cycles:
                for i in range(len(cycle) - 1):
                    dot_lines.append(f'    "{cycle[i]}" -> "{cycle[i+1]}" [color="red", penwidth=2];')
        
        dot_lines.append('}')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(dot_lines))
        
        print(f"✓ DOT 文件已生成：{output_path}")
    
    def generate_html(self, output_path: str, analysis_results: Dict):
        """生成 HTML 交互式图表"""
        import json as json_module
        
        # 准备节点数据
        nodes = []
        links = []
        
        color_map = {
            'core': '#4CAF50',
            'feature': '#2196F3',
            'app': '#FF9800',
            'unknown': '#9E9E9E',
        }
        
        for name, module in self.graph.modules.items():
            nodes.append({
                'id': name,
                'label': name.split('.')[-1],
                'group': module.layer,
                'full_name': name,
                'imports': len(module.imports),
                'imported_by': len(module.imported_by),
            })
        
        for name, module in self.graph.modules.items():
            for target in list(module.imports):
                if target in self.graph.modules:
                    links.append({
                        'source': name,
                        'target': target,
                    })
        
        nodes_json = json_module.dumps(nodes)
        links_json = json_module.dumps(links)
        
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模块依赖关系图 - 中国象棋</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.css" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Arial', sans-serif; 
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ 
            text-align: center; 
            color: #333; 
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{ 
            font-size: 32px; 
            font-weight: bold; 
            color: #2196F3;
        }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .warning {{ color: #f44336; }}
        .success {{ color: #4CAF50; }}
        #network {{ 
            height: 600px; 
            border: 1px solid #ddd; 
            border-radius: 8px;
            background: white;
            margin-bottom: 20px;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        .analysis {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        .analysis h2 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .analysis-section {{
            margin-bottom: 20px;
        }}
        .analysis-section h3 {{
            color: #666;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        .module-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .module-tag {{
            background: #f0f0f0;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            color: #333;
        }}
        .module-tag.danger {{
            background: #ffebee;
            color: #c62828;
        }}
        .module-tag.warning {{
            background: #fff3e0;
            color: #e65100;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f9f9f9;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ 模块依赖关系图 - 中国象棋项目</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{analysis_results['total_modules']}</div>
                <div class="stat-label">总模块数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {'warning' if analysis_results['cycles'] else 'success'}">
                    {len(analysis_results['cycles'])}
                </div>
                <div class="stat-label">循环依赖</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(analysis_results['isolated_modules'])}</div>
                <div class="stat-label">孤立模块</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(analysis_results['over_dependent_modules'])}</div>
                <div class="stat-label">过度依赖模块</div>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4CAF50;"></div>
                <span>核心层 (core)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2196F3;"></div>
                <span>功能层 (feature)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF9800;"></div>
                <span>应用层 (app)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #9E9E9E;"></div>
                <span>未知层级</span>
            </div>
        </div>
        
        <div id="network"></div>
        
        <div class="analysis">
            <h2>📊 依赖分析报告</h2>
            
            <div class="analysis-section">
                <h3>🔄 循环依赖 (需要重构)</h3>
                {self._generate_cycles_html(analysis_results['cycles'])}
            </div>
            
            <div class="analysis-section">
                <h3>📦 孤立模块 (无依赖关系)</h3>
                {self._generate_isolated_html(analysis_results['isolated_modules'])}
            </div>
            
            <div class="analysis-section">
                <h3>⚠️ 过度依赖模块 (导入过多)</h3>
                {self._generate_over_dependent_html(analysis_results['over_dependent_modules'])}
            </div>
            
            <div class="analysis-section">
                <h3>🎯 核心模块 (被频繁依赖)</h3>
                {self._generate_heavily_depended_html(analysis_results['heavily_depended_modules'])}
            </div>
            
            <div class="analysis-section">
                <h3>💡 重构建议</h3>
                {self._generate_recommendations(analysis_results)}
            </div>
        </div>
    </div>
    
    <script>
        const nodes = new vis.DataSet({nodes_json});
        const links = new vis.DataSet({links_json});
        
        const colors = {{
            core: '#4CAF50',
            feature: '#2196F3',
            app: '#FF9800',
            unknown: '#9E9E9E'
        }};
        
        const data = {{ nodes, edges: links }};
        const options = {{
            nodes: {{
                shape: 'box',
                font: {{
                    face: 'Arial',
                    size: 12
                }},
                margin: 10,
                borderWidth: 2
            }},
            edges: {{
                width: 1,
                color: {{ color: '#ccc', highlight: '#2196F3' }},
                smooth: {{ type: 'continuous' }}
            }},
            groups: {{
                core: {{ color: {{ background: colors.core, border: '#388E3C' }} }},
                feature: {{ color: {{ background: colors.feature, border: '#1976D2' }} }},
                app: {{ color: {{ background: colors.app, border: '#F57C00' }} }},
                unknown: {{ color: {{ background: colors.unknown, border: '#616161' }} }}
            }},
            physics: {{
                enabled: true,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09
                }},
                stabilization: {{ iterations: 100 }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            }}
        }};
        
        const network = new vis.Network(document.getElementById('network'), data, options);
        
        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                console.log('Selected node:', node);
            }}
        }});
    </script>
</body>
</html>'''
        
        # 写入 HTML 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML 文件已生成：{output_path}")
    
    def _generate_cycles_html(self, cycles: List[List[str]]) -> str:
        if not cycles:
            return '<p class="success">✅ 未发现循环依赖</p>'
        
        html = '<table><tr><th>#</th><th>循环路径</th><th>模块数</th></tr>'
        for i, cycle in enumerate(cycles, 1):
            path = ' → '.join([m.split('.')[-1] for m in cycle])
            html += f'<tr><td>{i}</td><td class="danger">{path}</td><td>{len(cycle)-1}</td></tr>'
        html += '</table>'
        return html
    
    def _generate_isolated_html(self, isolated: List[str]) -> str:
        if not isolated:
            return '<p class="success">✅ 无孤立模块</p>'
        
        modules = ''.join([f'<span class="module-tag">{m.split(".")[-1]}</span>' for m in isolated])
        return f'<div class="module-list">{modules}</div>'
    
    def _generate_over_dependent_html(self, over_dependent: List[Tuple[str, int]]) -> str:
        if not over_dependent:
            return '<p class="success">✅ 无过度依赖模块</p>'
        
        html = '<table><tr><th>模块</th><th>导入数量</th></tr>'
        for module, count in over_dependent:
            html += f'<tr><td class="warning">{module.split(".")[-1]}</td><td>{count}</td></tr>'
        html += '</table>'
        return html
    
    def _generate_heavily_depended_html(self, heavily_depended: List[Tuple[str, int]]) -> str:
        if not heavily_depended:
            return '<p>暂无高频被依赖模块</p>'
        
        html = '<table><tr><th>模块</th><th>被依赖次数</th></tr>'
        for module, count in heavily_depended:
            html += f'<tr><td>{module.split(".")[-1]}</td><td>{count}</td></tr>'
        html += '</table>'
        return html
    
    def _generate_recommendations(self, results: Dict) -> str:
        recommendations = []
        
        if results['cycles']:
            recommendations.append(
                '<strong class="danger">🔴 高优先级：</strong> 发现循环依赖，建议通过引入接口层或重构依赖方向来消除。'
            )
        
        if results['over_dependent_modules']:
            recommendations.append(
                '<strong class="warning">🟡 中优先级：</strong> 部分模块导入过多，考虑拆分为更小的模块或使用依赖注入。'
            )
        
        if results['isolated_modules']:
            recommendations.append(
                '<strong>🔵 低优先级：</strong> 发现孤立模块，检查是否为未使用代码或需要整合。'
            )
        
        if results['heavily_depended_modules']:
            recommendations.append(
                '<strong>💡 建议：</strong> 核心模块被频繁依赖，确保其 API 稳定并有完善的测试覆盖。'
            )
        
        if not recommendations:
            return '<p class="success">✅ 模块结构良好，无需重构</p>'
        
        return '<ul>' + ''.join([f'<li style="margin: 10px 0;">{r}</li>' for r in recommendations]) + '</ul>'


def main():
    """主函数"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='模块依赖分析工具')
    parser.add_argument('--root', default='src/backend', help='项目根目录')
    parser.add_argument('--output-dir', default='docs/architecture', help='输出目录')
    parser.add_argument('--format', choices=['all', 'dot', 'html', 'json'], default='all', help='输出格式')
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = DependencyAnalyzer(args.root)
    
    # 执行分析
    print("🚀 开始模块依赖分析...\n")
    results = analyzer.analyze()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出
    if args.format in ['all', 'dot']:
        analyzer.generate_dot(str(output_dir / 'dependencies.dot'))
    
    if args.format in ['all', 'html']:
        analyzer.generate_html(str(output_dir / 'dependency-graph.html'), results)
    
    if args.format in ['all', 'json']:
        with open(output_dir / 'dependency-analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ JSON 文件已生成：{output_dir / 'dependency-analysis.json'}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 分析摘要")
    print("="*60)
    print(f"总模块数：{results['total_modules']}")
    print(f"循环依赖：{len(results['cycles'])} 个")
    print(f"孤立模块：{len(results['isolated_modules'])} 个")
    print(f"过度依赖模块：{len(results['over_dependent_modules'])} 个")
    print(f"核心模块 (被频繁依赖): {len(results['heavily_depended_modules'])} 个")
    
    if results['cycles']:
        print("\n⚠️  发现循环依赖:")
        for i, cycle in enumerate(results['cycles'], 1):
            print(f"  {i}. {' -> '.join(cycle)}")
    
    print("\n✓ 分析完成!")


if __name__ == '__main__':
    main()
