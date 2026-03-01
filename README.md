# Terminal Snake Game

用 Python 编写的经典贪吃蛇游戏，支持终端运行。

## 功能特性

- **双版本**：
  - `snake_interactive.py` - 交互式版本，使用 curses 库，支持键盘实时控制
  - `snake.py` - 自动演示版本，带简单 AI 自动导航

- **游戏机制**：
  - 蛇初始长度为 3 节
  - 随机生成食物，不能与蛇体重叠
  - 速度随进度增加（每吃 5 个食物速度提升 15%）
  - 撞墙或撞自己则游戏结束

- **操作方式**：
  - `↑↓←→` 或 `WASD` - 方向控制
  - `空格` - 暂停/继续
  - `Q` 或 `Esc` - 退出游戏
  - `R` - 重新开始

## 环境要求

- Python 3.6+
- Linux/macOS：无需额外依赖
- Windows：需要安装 `windows-curses`

## 安装

```bash
# 克隆仓库
git clone https://github.com/morninghut/claude-snake-game.git
cd claude-snake-game
```

### Windows 额外安装

```bash
pip install windows-curses
```

## 运行

### 交互式版本（推荐）

```bash
python snake_interactive.py
```

### 自动演示版本

```bash
python snake.py
```

## 游戏界面

```
========================================
|                                    |
|           @  ooo  *                |
|                                    |
|          Score: 30 | Speed: 6.7/s  |
========================================
WASD/Arrows: Move | Space: Pause | Q: Quit | R: Restart
```

### 符号说明

| 符号 | 含义 |
|------|------|
| `@` | 蛇头（亮绿色）|
| `o` | 蛇身（绿色）|
| `*` | 食物（红色）|
| `#` | 墙壁（白色）|

## 项目结构

```
.
├── snake.py              # 自动演示版本
├── snake_interactive.py  # 交互式版本
├── SPEC.md              # 游戏规范文档
└── README.md            # 本文件
```

## 许可证

MIT License
