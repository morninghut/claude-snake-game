# Terminal Snake Game

用 Python 编写的经典贪吃蛇游戏，支持终端运行。

## 功能特性

### 游戏模式
- **Classic (c)** - 经典模式
- **Time Attack (t)** - 2分钟计时挑战
- **Zen (z)** - 禅模式（无限生命，穿墙）
- **Survival (s)** - 生存模式（障碍物随分数增加）

### 难度选择
- 简单 (200ms) / 中等 (150ms) / 困难 (100ms)

### 道具系统
- **◆/★** (红色) - 食物
- **◐** (紫色) - 减速道具
- **◑** (紫色) - 双倍分数
- **✦** (紫色) - 额外长度

### 视觉效果
- Unicode 字符支持（更美观的边框和符号）
- 食物脉冲动画
- 分数弹出效果
- 真彩色支持

### 其他
- 高分系统 - 本地持久化存储
- 音效开关
- 暂停功能

## 操作方式

- `↑↓←→` 或 `WASD` - 方向控制
- `空格` - 暂停/继续
- `Q` - 返回菜单
- `R` - 重新开始
- `1/2/3` - 选择难度
- `C/T/Z/S` - 选择游戏模式
- `M` - 开关音效
- `U` - 开关 Unicode

## 环境要求

- Python 3.6+
- Linux/macOS：无需额外依赖
- Windows：需要安装 `windows-curses`

## 安装

```bash
git clone https://github.com/morninghut/claude-snake-game.git
cd claude-snake-game
```

### Windows 额外安装

```bash
pip install windows-curses
```

## 运行

```bash
python snake_interactive.py
```

## 游戏界面

```
╔══════════════════════════════════════════╗
║                                          ║
║           ● ○○○ ◆                      ║
║                                          ║
║    Score: 30 | High: 50 | Speed: 10    ║
║                                          ║
╚══════════════════════════════════════════╝
WASD/Arrows: Move | Space: Pause | R: Restart | Q: Menu
```

## 项目结构

```
.
├── snake.py              # 自动演示版本（AI）
├── snake_interactive.py  # 交互式版本（推荐）
├── SPEC.md              # 游戏规范文档
└── README.md            # 本文件
```

## 更新日志

### v2.1 (Latest)
- **新增游戏模式**：Classic、Time Attack、Zen、Survival
- **Unicode 支持**：更美观的边框和符号
- **视觉效果**：食物脉冲动画、分数弹出
- **音效增强**：可开关音效
- **配置持久化**：保存音效和 Unicode 设置

### v2.0
- 添加难度选择系统
- 添加高分持久化
- 添加道具系统
- 添加音效反馈
- 添加游戏菜单
- 优化输入处理

### v1.0
- 初始版本
- 基础贪吃蛇玩法

## 许可证

MIT License
