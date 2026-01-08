# smart_miner_web.py
from flask import Flask, render_template_string, jsonify, request
import heapq
import threading
import time
import atexit

app = Flask(__name__)

# HTML шаблон
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Умный робот-шахтёр</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .content {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 20px;
            padding: 20px;
        }

        .maze-container {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .maze-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 1px;
            background: #e9ecef;
            padding: 1px;
            border-radius: 5px;
        }

        .cell {
            width: 32px;
            height: 32px;
            border-radius: 3px;
            position: relative;
            cursor: pointer;
            transition: transform 0.1s;
        }

        .cell:hover {
            transform: scale(1.1);
            z-index: 1;
            box-shadow: 0 0 5px rgba(0,0,0,0.2);
        }

        .cell.path { background-color: white; }
        .cell.ore { background-color: #8B7355; }
        .cell.processed { background-color: #90EE90; }
        .cell.wall { background-color: #2F4F4F; }
        .cell.danger { background-color: #FF6B6B; }
        .cell.finish { background-color: #4169E1; }
        .cell.mine { background-color: #8B4513; }
        .cell.visited { border: 2px solid #FFD700; }

        .robot {
            position: absolute;
            width: 20px;
            height: 20px;
            background: radial-gradient(circle at 30% 30%, #FFA500, #FF8C00);
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
            border: 2px solid #FF8C00;
        }

        .robot::after {
            content: '';
            position: absolute;
            width: 5px;
            height: 5px;
            background: black;
            border-radius: 50%;
            top: 30%;
            left: 30%;
        }

        .control-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .panel-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
        }

        .panel-section h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 16px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }

        .cell-types {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }

        .cell-type {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .cell-type:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }

        .cell-type.selected {
            border-color: #667eea;
            background: #667eea;
            color: white;
        }

        .color-box {
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid #ccc;
        }

        .move-controls {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 5px;
        }

        .move-btn {
            padding: 10px;
            border: none;
            border-radius: 5px;
            background: #667eea;
            color: white;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.2s;
        }

        .move-btn:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }

        .move-btn:active {
            transform: translateY(0);
        }

        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .action-btn {
            padding: 10px;
            border: none;
            border-radius: 5px;
            background: #48bb78;
            color: white;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }

        .action-btn:hover {
            background: #38a169;
        }

        .auto-buttons {
            display: flex;
            gap: 10px;
        }

        .auto-btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 5px;
            color: white;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.2s;
        }

        .start-btn {
            background: #38a169;
        }

        .stop-btn {
            background: #e53e3e;
        }

        .reset-btn {
            background: #ed8936;
        }

        .stats-panel {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
        }

        .stats-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }

        .stats-item:last-child {
            border-bottom: none;
        }

        .status {
            padding: 10px;
            background: #e6fffa;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            color: #234e52;
        }

        .legend {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 10px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
        }

        .legend-color {
            width: 15px;
            height: 15px;
            border-radius: 3px;
            border: 1px solid #ccc;
        }

        .info-panel {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            grid-column: 1 / -1;
        }

        @media (max-width: 1024px) {
            .content {
                grid-template-columns: 1fr;
            }
            
            .maze-grid {
                grid-template-columns: repeat(12, 1fr);
            }
            
            .cell {
                width: 28px;
                height: 28px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Умный робот-шахтёр</h1>
            <p>Интеллектуальное управление горнодобывающим роботом</p>
        </div>
        
        <div class="content">
            <div class="maze-container">
                <div id="maze" class="maze-grid">
                    <!-- Maze will be generated here -->
                </div>
            </div>
            
            <div class="control-panel">
                <div class="panel-section">
                    <h3>Тип клетки</h3>
                    <div class="cell-types" id="cellTypes">
                        <!-- Cell types will be generated here -->
                    </div>
                </div>
                
                <div class="panel-section">
                    <h3>Управление</h3>
                    <div class="move-controls">
                        <button class="move-btn" onclick="moveRobot('up')">↖</button>
                        <button class="move-btn" onclick="moveRobot('forward')">↑</button>
                        <button class="move-btn" onclick="moveRobot('left')">←</button>
                        <button class="move-btn" onclick="moveRobot('right')">→</button>
                        <button class="move-btn" onclick="moveRobot('down')">↘</button>
                        <button class="move-btn" onclick="moveRobot('backward')">↓</button>
                    </div>
                    
                    <div class="action-buttons" style="margin-top: 10px;">
                        <button class="action-btn" onclick="performAction('process_ore')">
                            ⛏️ Обработать руду
                        </button>
                        <button class="action-btn" onclick="performAction('convert_to_ore')">
                            🪨 Создать руду
                        </button>
                    </div>
                </div>
                
                <div class="panel-section">
                    <h3>Авторежим</h3>
                    <div class="auto-buttons">
                        <button class="auto-btn start-btn" onclick="startAuto()">
                            ▶ Умный обход
                        </button>
                        <button class="auto-btn stop-btn" onclick="stopAuto()">
                            ⏹ Стоп
                        </button>
                    </div>
                    <button class="auto-btn reset-btn" style="margin-top: 10px;" onclick="resetMaze()">
                        🔄 Сброс
                    </button>
                </div>
                
                <div class="panel-section">
                    <h3>Статистика</h3>
                    <div class="stats-panel">
                        <div class="stats-item">
                            <span>Позиция робота:</span>
                            <span id="robotPos">0, 0</span>
                        </div>
                        <div class="stats-item">
                            <span>Обработано руды:</span>
                            <span id="processedCount">0</span>
                        </div>
                        <div class="stats-item">
                            <span>Осталось руды:</span>
                            <span id="oreRemaining">0</span>
                        </div>
                        <div class="stats-item">
                            <span>Шагов:</span>
                            <span id="moveCount">0</span>
                        </div>
                        <div class="status" id="status">Готов</div>
                    </div>
                </div>
            </div>
            
            <div class="info-panel">
                <div class="legend">
                    <div class="legend-item"><div class="legend-color" style="background: orange;"></div><span>Робот</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: white;"></div><span>Путь</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #8B7355;"></div><span>Руда</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #90EE90;"></div><span>Обработано</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #2F4F4F;"></div><span>Забой</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #FF6B6B;"></div><span>Опасно</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #4169E1;"></div><span>Финиш</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #8B4513;"></div><span>Шахта</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #FFFACD; border: 2px solid #FFD700;"></div><span>Посещено</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedCellType = 'PATH';
        let updateInterval = null;
        
        // Цвета клеток
        const cellColors = {
            'PATH': 'path',
            'ORE': 'ore',
            'PROCESSED': 'processed',
            'WALL': 'wall',
            'DANGER': 'danger',
            'FINISH': 'finish',
            'MINE': 'mine'
        };
        
        // Инициализация выбора типа клетки
        function initCellTypes() {
            const cellTypes = [
                {name: 'Путь', type: 'PATH', color: 'white'},
                {name: 'Руда', type: 'ORE', color: '#8B7355'},
                {name: 'Забой', type: 'WALL', color: '#2F4F4F'},
                {name: 'Опасно', type: 'DANGER', color: '#FF6B6B'},
                {name: 'Финиш', type: 'FINISH', color: '#4169E1'},
                {name: 'Шахта', type: 'MINE', color: '#8B4513'}
            ];
            
            const container = document.getElementById('cellTypes');
            cellTypes.forEach(item => {
                const div = document.createElement('div');
                div.className = 'cell-type';
                if (item.type === selectedCellType) {
                    div.classList.add('selected');
                }
                
                div.innerHTML = `
                    <div class="color-box" style="background: ${item.color};"></div>
                    <span>${item.name}</span>
                `;
                
                div.onclick = () => {
                    document.querySelectorAll('.cell-type').forEach(el => {
                        el.classList.remove('selected');
                    });
                    div.classList.add('selected');
                    selectedCellType = item.type;
                };
                
                container.appendChild(div);
            });
        }
        
        // Загрузка состояния
        async function loadState() {
            try {
                const response = await fetch('/api/state');
                const data = await response.json();
                renderMaze(data);
                updateStats(data);
            } catch (error) {
                console.error('Error loading state:', error);
            }
        }
        
        // Отрисовка лабиринта
        function renderMaze(state) {
            const mazeElement = document.getElementById('maze');
            mazeElement.innerHTML = '';
            
            // Устанавливаем размеры сетки
            mazeElement.style.gridTemplateColumns = `repeat(${state.width}, 1fr)`;
            
            // Отрисовываем клетки
            state.cells.forEach(row => {
                row.forEach(cell => {
                    const cellElement = document.createElement('div');
                    cellElement.className = `cell ${cellColors[cell.type]}`;
                    
                    if (cell.visited) {
                        cellElement.classList.add('visited');
                    }
                    
                    if (cell.has_robot) {
                        const robotElement = document.createElement('div');
                        robotElement.className = 'robot';
                        cellElement.appendChild(robotElement);
                    }
                    
                    cellElement.onclick = () => updateCell(cell.x, cell.y);
                    mazeElement.appendChild(cellElement);
                });
            });
        }
        
        // Обновление статистики
        function updateStats(state) {
            document.getElementById('robotPos').textContent = 
                `${state.robot.x}, ${state.robot.y}`;
            document.getElementById('processedCount').textContent = 
                state.stats.processed;
            document.getElementById('oreRemaining').textContent = 
                state.stats.ore_remaining;
            document.getElementById('moveCount').textContent = 
                state.stats.moves;
            
            document.getElementById('status').textContent = 
                state.auto_running ? 'Автообход...' : 'Готов';
            document.getElementById('status').style.background = 
                state.auto_running ? '#fed7d7' : '#e6fffa';
            document.getElementById('status').style.color = 
                state.auto_running ? '#742a2a' : '#234e52';
        }
        
        // Движение робота
        async function moveRobot(direction) {
            try {
                const response = await fetch('/api/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({direction: direction})
                });
                
                if (response.ok) {
                    loadState();
                } else {
                    const error = await response.json();
                    alert(`Ошибка: ${error.error}`);
                }
            } catch (error) {
                console.error('Error moving robot:', error);
            }
        }
        
        // Выполнение действия
        async function performAction(action) {
            try {
                const response = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: action})
                });
                
                if (response.ok) {
                    loadState();
                }
            } catch (error) {
                console.error('Error performing action:', error);
            }
        }
        
        // Обновление клетки
        async function updateCell(x, y) {
            try {
                const response = await fetch('/api/cell', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({x: x, y: y, type: selectedCellType})
                });
                
                if (response.ok) {
                    loadState();
                }
            } catch (error) {
                console.error('Error updating cell:', error);
            }
        }
        
        // Запуск авторежима
        async function startAuto() {
            try {
                const response = await fetch('/api/auto/start', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    startAutoUpdate();
                }
            } catch (error) {
                console.error('Error starting auto mode:', error);
            }
        }
        
        // Остановка авторежима
        async function stopAuto() {
            try {
                const response = await fetch('/api/auto/stop', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    stopAutoUpdate();
                    loadState();
                }
            } catch (error) {
                console.error('Error stopping auto mode:', error);
            }
        }
        
        // Сброс лабиринта
        async function resetMaze() {
            try {
                const response = await fetch('/api/reset', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    loadState();
                }
            } catch (error) {
                console.error('Error resetting maze:', error);
            }
        }
        
        // Автообновление при авторежиме
        function startAutoUpdate() {
            stopAutoUpdate();
            updateInterval = setInterval(loadState, 300);
        }
        
        function stopAutoUpdate() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }
        
        // Инициализация при загрузке
        window.onload = function() {
            initCellTypes();
            loadState();
            
            // Проверяем состояние каждые 2 секунды
            setInterval(loadState, 2000);
        };
    </script>
</body>
</html>'''

# Классы из main.py (упрощенная версия)
class MineDirectionType:
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"

class MineCellType:
    PATH = "PATH"
    ORE = "ORE"
    PROCESSED = "PROCESSED"
    WALL = "WALL"
    DANGER = "DANGER"
    FINISH = "FINISH"
    MINE = "MINE"

class MineCell:
    def __init__(self, x, y, cell_type=MineCellType.PATH):
        self.x = x
        self.y = y
        self.cell_type = cell_type
        self.has_robot = False

class MineMaze:
    def __init__(self, width=12, height=10):
        self.width = width
        self.height = height
        self.cells = [[MineCell(x, y) for y in range(height)] for x in range(width)]
    
    def initialize_maze(self, default_type=MineCellType.PATH):
        for x in range(self.width):
            for y in range(self.height):
                self.cells[x][y].cell_type = default_type
    
    def get_adjacent_cell(self, cell, direction):
        x, y = cell.x, cell.y
        
        if direction == MineDirectionType.FORWARD:
            if y - 1 >= 0:
                return self.cells[x][y - 1]
        elif direction == MineDirectionType.BACKWARD:
            if y + 1 < self.height:
                return self.cells[x][y + 1]
        elif direction == MineDirectionType.LEFT:
            if x - 1 >= 0:
                return self.cells[x - 1][y]
        elif direction == MineDirectionType.RIGHT:
            if x + 1 < self.width:
                return self.cells[x + 1][y]
        elif direction == MineDirectionType.UP:
            # В 2D лабиринте UP/DOWN могут быть реализованы как специальные переходы
            # Для простоты считаем, что они работают как FORWARD/BACKWARD
            if y - 1 >= 0:
                return self.cells[x][y - 1]
        elif direction == MineDirectionType.DOWN:
            if y + 1 < self.height:
                return self.cells[x][y + 1]
        return None

class RobotMiner:
    def __init__(self, maze):
        self.maze = maze
        self.current_cell = maze.cells[0][0]
        self.current_cell.has_robot = True
    
    def move_to(self, direction):
        next_cell = self.maze.get_adjacent_cell(self.current_cell, direction)
        if next_cell and next_cell.cell_type not in [MineCellType.WALL, MineCellType.DANGER]:
            self.current_cell.has_robot = False
            next_cell.has_robot = True
            self.current_cell = next_cell
            return next_cell
        return None
    
    def go_forward(self):
        return self.move_to(MineDirectionType.FORWARD)
    
    def go_backward(self):
        return self.move_to(MineDirectionType.BACKWARD)
    
    def shift_left(self):
        return self.move_to(MineDirectionType.LEFT)
    
    def shift_right(self):
        return self.move_to(MineDirectionType.RIGHT)
    
    def go_up(self):
        return self.move_to(MineDirectionType.UP)
    
    def go_down(self):
        return self.move_to(MineDirectionType.DOWN)
    
    def process_ore(self):
        if self.current_cell.cell_type == MineCellType.ORE:
            self.current_cell.cell_type = MineCellType.PROCESSED
            return True
        return False
    
    def convert_path_to_ore(self):
        if self.current_cell.cell_type == MineCellType.PATH:
            self.current_cell.cell_type = MineCellType.ORE
            return True
        return False

# Класс для веб-приложения
class SmartWebRobot:
    def __init__(self):
        self.maze = MineMaze(12, 10)
        self.maze.initialize_maze(MineCellType.PATH)
        self.maze.cells[11][9].cell_type = MineCellType.FINISH
        self.create_maze()
        
        self.robot = RobotMiner(self.maze)
        self.visited_cells = set()
        self.auto_running = False
        self.auto_thread = None
        
        # Статистика
        self.stats = {
            'processed': 0,
            'moves': 0,
            'ore_remaining': 0
        }
    
    def create_maze(self):
        """Создает лабиринт"""
        # Стены
        walls = [
            (2, 3), (3, 3), (4, 3),
            (7, 1), (7, 2), (7, 3), (7, 4),
            (5, 6), (5, 7), (5, 8),
            (9, 5), (10, 5), (11, 5)
        ]
        
        # Руда
        ores = [
            (1, 6), (2, 6), (3, 6),
            (8, 2), (8, 3), (8, 4),
            (4, 8), (6, 8),
            (10, 7), (10, 8)
        ]
        
        # Опасные зоны
        dangers = [
            (2, 8), (6, 1),
            (9, 1), (9, 9)
        ]
        
        for x, y in walls:
            self.maze.cells[x][y].cell_type = MineCellType.WALL
            
        for x, y in ores:
            self.maze.cells[x][y].cell_type = MineCellType.ORE
            
        for x, y in dangers:
            self.maze.cells[x][y].cell_type = MineCellType.DANGER
        
        # Шахты
        self.maze.cells[0][9].cell_type = MineCellType.MINE
        self.maze.cells[6][5].cell_type = MineCellType.MINE
    
    def heuristic(self, a, b):
        """Эвристика для A*"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def a_star_search(self, start, goal):
        """Поиск пути A*"""
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == goal:
                break
            
            # Получаем соседей
            for direction in [MineDirectionType.FORWARD, MineDirectionType.BACKWARD,
                            MineDirectionType.LEFT, MineDirectionType.RIGHT]:
                cell = self.maze.cells[current[0]][current[1]]
                neighbor = self.maze.get_adjacent_cell(cell, direction)
                
                if neighbor is None:
                    continue
                
                # Проверяем, можно ли пройти
                if neighbor.cell_type in (MineCellType.WALL, MineCellType.DANGER):
                    continue
                
                next_cell = (neighbor.x, neighbor.y)
                new_cost = cost_so_far[current] + 1
                
                if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
                    cost_so_far[next_cell] = new_cost
                    priority = new_cost + self.heuristic(goal, next_cell)
                    heapq.heappush(frontier, (priority, next_cell))
                    came_from[next_cell] = current
        
        # Восстанавливаем путь
        if goal not in came_from:
            return None
        
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        
        path.append(start)
        path.reverse()
        return path
    
    def find_nearest_ore(self, start):
        """Находит ближайшую необработанную руду"""
        queue = [(start, 0)]
        visited = set([start])
        
        while queue:
            (x, y), distance = queue.pop(0)
            cell = self.maze.cells[x][y]
            
            if cell.cell_type == MineCellType.ORE:
                return (x, y)
            
            # Добавляем соседей
            for direction in [MineDirectionType.FORWARD, MineDirectionType.BACKWARD,
                            MineDirectionType.LEFT, MineDirectionType.RIGHT]:
                neighbor = self.maze.get_adjacent_cell(cell, direction)
                if neighbor is None:
                    continue
                
                next_cell = (neighbor.x, neighbor.y)
                if (next_cell not in visited and 
                    neighbor.cell_type not in (MineCellType.WALL, MineCellType.DANGER)):
                    visited.add(next_cell)
                    queue.append((next_cell, distance + 1))
        
        return None
    
    def start_smart_traversal(self):
        """Запускает умный обход в отдельном потоке"""
        self.auto_running = True
        
        def smart_task():
            while self.auto_running:
                start = (self.robot.current_cell.x, self.robot.current_cell.y)
                ore_pos = self.find_nearest_ore(start)
                
                if ore_pos:
                    # Идем к руде
                    path = self.a_star_search(start, ore_pos)
                    if path and len(path) > 1:
                        for next_pos in path[1:]:
                            if not self.auto_running:
                                break
                            
                            # Перемещаем робота
                            self.robot.current_cell.has_robot = False
                            next_cell = self.maze.cells[next_pos[0]][next_pos[1]]
                            next_cell.has_robot = True
                            self.robot.current_cell = next_cell
                            self.visited_cells.add(next_pos)
                            self.stats['moves'] += 1
                            
                            # Обрабатываем клетку
                            if next_cell.cell_type == MineCellType.ORE:
                                self.robot.process_ore()
                                self.stats['processed'] += 1
                            elif next_cell.cell_type == MineCellType.PATH:
                                self.robot.convert_path_to_ore()
                            
                            time.sleep(0.3)
                else:
                    # Ищем финиш
                    finish_pos = None
                    for x in range(self.maze.width):
                        for y in range(self.maze.height):
                            if self.maze.cells[x][y].cell_type == MineCellType.FINISH:
                                finish_pos = (x, y)
                                break
                    
                    if finish_pos:
                        path = self.a_star_search(start, finish_pos)
                        if path and len(path) > 1:
                            for next_pos in path[1:]:
                                if not self.auto_running:
                                    break
                                
                                # Перемещаем робота
                                self.robot.current_cell.has_robot = False
                                next_cell = self.maze.cells[next_pos[0]][next_pos[1]]
                                next_cell.has_robot = True
                                self.robot.current_cell = next_cell
                                self.visited_cells.add(next_pos)
                                self.stats['moves'] += 1
                                
                                time.sleep(0.3)
                    
                    self.auto_running = False
                    break
        
        self.auto_thread = threading.Thread(target=smart_task, daemon=True)
        self.auto_thread.start()
    
    def stop_traversal(self):
        self.auto_running = False
    
    def reset(self):
        self.auto_running = False
        if self.auto_thread and self.auto_thread.is_alive():
            self.auto_thread.join(timeout=1)
        
        self.maze = MineMaze(12, 10)
        self.maze.initialize_maze(MineCellType.PATH)
        self.maze.cells[11][9].cell_type = MineCellType.FINISH
        self.create_maze()
        
        self.robot = RobotMiner(self.maze)
        self.visited_cells.clear()
        self.stats = {'processed': 0, 'moves': 0, 'ore_remaining': 0}
    
    def get_state(self):
        """Возвращает состояние лабиринта для JSON"""
        cells = []
        ore_count = 0
        
        for y in range(self.maze.height):
            row = []
            for x in range(self.maze.width):
                cell = self.maze.cells[x][y]
                cell_data = {
                    'type': cell.cell_type,
                    'has_robot': cell.has_robot,
                    'visited': (x, y) in self.visited_cells,
                    'x': x,
                    'y': y
                }
                row.append(cell_data)
                
                if cell.cell_type == MineCellType.ORE:
                    ore_count += 1
            cells.append(row)
        
        self.stats['ore_remaining'] = ore_count
        
        return {
            'cells': cells,
            'robot': {
                'x': self.robot.current_cell.x,
                'y': self.robot.current_cell.y
            },
            'stats': self.stats,
            'auto_running': self.auto_running,
            'width': self.maze.width,
            'height': self.maze.height
        }

# Создаем глобальный экземпляр робота
robot_system = SmartWebRobot()

# Маршруты Flask
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(robot_system.get_state())

@app.route('/api/move', methods=['POST'])
def move_robot():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    direction = data.get('direction')
    
    if direction == 'forward':
        result = robot_system.robot.go_forward()
    elif direction == 'backward':
        result = robot_system.robot.go_backward()
    elif direction == 'left':
        result = robot_system.robot.shift_left()
    elif direction == 'right':
        result = robot_system.robot.shift_right()
    elif direction == 'up':
        result = robot_system.robot.go_up()
    elif direction == 'down':
        result = robot_system.robot.go_down()
    else:
        return jsonify({'error': 'Invalid direction'}), 400
    
    if result:
        robot_system.visited_cells.add((result.x, result.y))
        robot_system.stats['moves'] += 1
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Cannot move'}), 400

@app.route('/api/action', methods=['POST'])
def perform_action():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    action = data.get('action')
    
    if action == 'process_ore':
        if robot_system.robot.process_ore():
            robot_system.stats['processed'] += 1
    elif action == 'convert_to_ore':
        robot_system.robot.convert_path_to_ore()
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    return jsonify({'success': True})

@app.route('/api/cell', methods=['POST'])
def update_cell():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    x = data.get('x')
    y = data.get('y')
    cell_type = data.get('type')
    
    if x is None or y is None or cell_type is None:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        cell_type_enum = getattr(MineCellType, cell_type)
        robot_system.maze.cells[x][y].cell_type = cell_type_enum
        return jsonify({'success': True})
    except AttributeError:
        return jsonify({'error': 'Invalid cell type'}), 400

@app.route('/api/auto/start', methods=['POST'])
def start_auto():
    if robot_system.auto_running:
        return jsonify({'error': 'Already running'}), 400
    
    robot_system.start_smart_traversal()
    return jsonify({'success': True})

@app.route('/api/auto/stop', methods=['POST'])
def stop_auto():
    robot_system.stop_traversal()
    return jsonify({'success': True})

@app.route('/api/reset', methods=['POST'])
def reset():
    robot_system.reset()
    return jsonify({'success': True})

def cleanup():
    robot_system.stop_traversal()
    print("Сервер завершает работу...")

atexit.register(cleanup)

if __name__ == '__main__':
    app.run(debug=False, port=5003, host='0.0.0.0', threaded=True)
