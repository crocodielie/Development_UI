# smart_gui_tkinter.py
import tkinter as tk
from tkinter import ttk, messagebox
from enum import Enum
import time
import threading
from queue import PriorityQueue
from main import *

class SmartMineMazeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Умный робот-шахтёр")
        self.root.geometry("900x650")
        
        # Цвета для типов клеток
        self.colors = {
            MineCellType.PATH: "white",
            MineCellType.ORE: "#8B7355",
            MineCellType.PROCESSED: "#90EE90",
            MineCellType.WALL: "#2F4F4F",
            MineCellType.DANGER: "#FF6B6B",
            MineCellType.FINISH: "#4169E1",
            MineCellType.MINE: "#8B4513"
        }
        
        # Создаем лабиринт 10x10
        self.maze = MineMaze(12, 10)
        self.maze.initialize_maze(MineCellType.PATH)
        
        # Устанавливаем финиш
        self.maze.cells[11][9].cell_type = MineCellType.FINISH
        
        # Создаем более интересный лабиринт
        self.create_interesting_maze()
        
        self.robot = RobotMiner(self.maze)
        self.visited_cells = set()
        self.auto_running = False
        self.cell_size = 40
        
        self.setup_ui()
        self.draw_maze()
        
    def create_interesting_maze(self):
        """Создает лабиринт с препятствиями и ресурсами"""
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
        
        # Устанавливаем типы клеток
        for x, y in walls:
            self.maze.cells[x][y].cell_type = MineCellType.WALL
            
        for x, y in ores:
            self.maze.cells[x][y].cell_type = MineCellType.ORE
            
        for x, y in dangers:
            self.maze.cells[x][y].cell_type = MineCellType.DANGER
        
        # Несколько шахт
        self.maze.cells[0][9].cell_type = MineCellType.MINE
        self.maze.cells[6][5].cell_type = MineCellType.MINE
        
    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Canvas для лабиринта
        self.canvas = tk.Canvas(main_frame, width=480, height=400, bg="white", 
                               relief=tk.SUNKEN, borderwidth=1)
        self.canvas.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Панель управления (справа)
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.grid(row=0, column=1, sticky=tk.N)
        
        # Типы клеток
        type_frame = ttk.LabelFrame(control_frame, text="Тип клетки", padding="5")
        type_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        self.cell_type_var = tk.StringVar(value="PATH")
        cell_types = [
            ("Путь", "PATH", "white"),
            ("Руда", "ORE", "#8B7355"),
            ("Забой", "WALL", "#2F4F4F"),
            ("Опасно", "DANGER", "#FF6B6B"),
            ("Финиш", "FINISH", "#4169E1"),
            ("Шахта", "MINE", "#8B4513")
        ]
        
        for i, (text, value, color) in enumerate(cell_types):
            frame = ttk.Frame(type_frame)
            frame.grid(row=i, column=0, sticky=tk.W, pady=2)
            
            color_canvas = tk.Canvas(frame, width=20, height=20, bg=color, 
                                    highlightthickness=1, highlightbackground="gray")
            color_canvas.grid(row=0, column=0)
            
            rb = ttk.Radiobutton(frame, text=text, value=value,
                               variable=self.cell_type_var)
            rb.grid(row=0, column=1, padx=5)
        
        # Управление
        control_buttons = [
            ("↑", self.go_forward, 0, 1),
            ("←", self.shift_left, 1, 0),
            ("→", self.shift_right, 1, 2),
            ("↓", self.go_backward, 2, 1),
            ("↖", self.go_up, 0, 0),
            ("↘", self.go_down, 2, 2)
        ]
        
        move_frame = ttk.LabelFrame(control_frame, text="Управление", padding="10")
        move_frame.grid(row=1, column=0, pady=(0, 10))
        
        for text, command, row, col in control_buttons:
            btn = ttk.Button(move_frame, text=text, width=3, command=command)
            btn.grid(row=row, column=col, padx=2, pady=2)
        
        # Действия
        action_frame = ttk.LabelFrame(control_frame, text="Действия", padding="5")
        action_frame.grid(row=2, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(action_frame, text="⛏️ Обработать руду", 
                  command=self.process_ore).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="🪨 Создать руду", 
                  command=self.convert_to_ore).pack(fill=tk.X, pady=2)
        
        # Авторежим
        auto_frame = ttk.LabelFrame(control_frame, text="Авторежим", padding="5")
        auto_frame.grid(row=3, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(auto_frame, text="▶ Умный обход", 
                  command=self.start_smart_traversal).pack(fill=tk.X, pady=2)
        ttk.Button(auto_frame, text="⏹ Остановить", 
                  command=self.stop_auto_traversal).pack(fill=tk.X, pady=2)
        ttk.Button(auto_frame, text="🔄 Сброс", 
                  command=self.reset_maze).pack(fill=tk.X, pady=2)
        
        # Информация
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.info_label = ttk.Label(info_frame, text="Робот: (0, 0) | Обработано: 0 | Статус: Готов")
        self.info_label.pack()
        
        # Легенда
        legend_frame = ttk.Frame(info_frame)
        legend_frame.pack(pady=5)
        
        colors_info = [
            ("Робот", "orange"),
            ("Путь", "white"),
            ("Руда", "#8B7355"),
            ("Обработано", "#90EE90"),
            ("Забой", "#2F4F4F"),
            ("Опасно", "#FF6B6B"),
            ("Финиш", "#4169E1"),
            ("Шахта", "#8B4513"),
            ("Посещено", "#FFFACD")
        ]
        
        for i, (text, color) in enumerate(colors_info):
            if i % 4 == 0 and i > 0:
                ttk.Frame(legend_frame).pack()  # новая строка
            
            frame = ttk.Frame(legend_frame)
            frame.pack(side=tk.LEFT, padx=5)
            
            tk.Canvas(frame, width=15, height=15, bg=color, 
                     highlightthickness=1).pack(side=tk.LEFT)
            ttk.Label(frame, text=text, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Обработка кликов
        self.canvas.bind("<Button-1>", self.on_cell_click)
        
    def draw_maze(self):
        self.canvas.delete("all")
        
        for x in range(self.maze.width):
            for y in range(self.maze.height):
                cell = self.maze.cells[x][y]
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                # Цвет клетки
                color = self.colors.get(cell.cell_type, "white")
                
                # Если клетка посещена, добавляем оттенок
                if (x, y) in self.visited_cells:
                    if color == "white":
                        color = "#FFFACD"
                    elif color == "#8B7355":
                        color = "#A0522D"
                
                # Рисуем клетку
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=color, outline="#D3D3D3", width=1)
                
                # Робот
                if cell.has_robot:
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    radius = self.cell_size / 3
                    
                    # Рисуем робота как круг с ободком
                    self.canvas.create_oval(
                        center_x - radius, center_y - radius,
                        center_x + radius, center_y + radius,
                        fill="orange", outline="#FF8C00", width=2
                    )
                    
                    # Глаз робота
                    eye_radius = radius / 4
                    self.canvas.create_oval(
                        center_x - eye_radius, center_y - eye_radius,
                        center_x + eye_radius, center_y + eye_radius,
                        fill="black", outline=""
                    )
    
    def on_cell_click(self, event):
        if self.auto_running:
            return
            
        x = event.x // self.cell_size
        y = event.y // self.cell_size
        
        if 0 <= x < self.maze.width and 0 <= y < self.maze.height:
            cell_type_name = self.cell_type_var.get()
            cell_type = getattr(MineCellType, cell_type_name)
            self.maze.cells[x][y].cell_type = cell_type
            self.draw_maze()
    
    def move_robot_and_update(self, move_func):
        if self.auto_running:
            return
            
        old_pos = (self.robot.current_cell.x, self.robot.current_cell.y)
        result = move_func()
        
        if result:
            self.visited_cells.add((result.x, result.y))
            self.update_info()
            self.draw_maze()
        else:
            messagebox.showwarning("Ошибка", "Невозможно переместиться!")
    
    def go_forward(self):
        self.move_robot_and_update(self.robot.go_forward)
    
    def go_backward(self):
        self.move_robot_and_update(self.robot.go_backward)
    
    def shift_left(self):
        self.move_robot_and_update(self.robot.shift_left)
    
    def shift_right(self):
        self.move_robot_and_update(self.robot.shift_right)
    
    def go_up(self):
        self.move_robot_and_update(self.robot.go_up)
    
    def go_down(self):
        self.move_robot_and_update(self.robot.go_down)
    
    def process_ore(self):
        self.robot.process_ore()
        self.update_info()
        self.draw_maze()
    
    def convert_to_ore(self):
        self.robot.convert_path_to_ore()
        self.update_info()
        self.draw_maze()
    
    def update_info(self):
        x, y = self.robot.current_cell.x, self.robot.current_cell.y
        
        # Считаем обработанную руду
        processed_count = 0
        ore_count = 0
        for x_idx in range(self.maze.width):
            for y_idx in range(self.maze.height):
                cell = self.maze.cells[x_idx][y_idx]
                if cell.cell_type == MineCellType.PROCESSED:
                    processed_count += 1
                elif cell.cell_type == MineCellType.ORE:
                    ore_count += 1
        
        status = "Готов"
        if self.auto_running:
            status = "Автообход..."
        
        self.info_label.config(
            text=f"Робот: ({x}, {y}) | Обработано: {processed_count} | Руда осталась: {ore_count} | Статус: {status}"
        )
    
    def heuristic(self, a, b):
        """Эвристика для A* (манхэттенское расстояние)"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def a_star_search(self, start, goal):
        """Поиск пути A*"""
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while not frontier.empty():
            current = frontier.get()[1]
            
            if current == goal:
                break
            
            # Получаем соседей
            for direction in [MineDirectionType.FORWARD, MineDirectionType.BACKWARD,
                            MineDirectionType.LEFT, MineDirectionType.RIGHT,
                            MineDirectionType.DIAG_UP, MineDirectionType.DIAG_DOWN]:
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
                    frontier.put((priority, next_cell))
                    came_from[next_cell] = current
        
        # Восстанавливаем путь
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from.get(current)
            if current is None:
                return None  # Путь не найден
        
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
        """Запускает умный обход"""
        if self.auto_running:
            return
            
        self.auto_running = True
        self.visited_cells.clear()
        
        def smart_task():
            while self.auto_running:
                # Проверяем, есть ли необработанная руда
                start = (self.robot.current_cell.x, self.robot.current_cell.y)
                ore_pos = self.find_nearest_ore(start)
                
                if ore_pos:
                    # Идем к руде
                    path = self.a_star_search(start, ore_pos)
                    if path and len(path) > 1:
                        # Идем по пути
                        for next_pos in path[1:]:
                            if not self.auto_running:
                                break
                            
                            # Перемещаем робота
                            self.robot.current_cell.has_robot = False
                            next_cell = self.maze.cells[next_pos[0]][next_pos[1]]
                            next_cell.has_robot = True
                            self.robot.current_cell = next_cell
                            self.visited_cells.add(next_pos)
                            
                            # Обрабатываем клетку
                            if next_cell.cell_type == MineCellType.ORE:
                                self.robot.process_ore()
                            elif next_cell.cell_type == MineCellType.PATH:
                                self.robot.convert_path_to_ore()
                            
                            self.root.after(0, self.update_info)
                            self.root.after(0, self.draw_maze)
                            time.sleep(0.2)
                else:
                    # Идем к финишу
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
                                
                                self.root.after(0, self.update_info)
                                self.root.after(0, self.draw_maze)
                                time.sleep(0.2)
                    
                    # Достигли финиша или нет пути
                    self.root.after(0, lambda: messagebox.showinfo("Завершено", 
                        "Вся руда обработана! Робот достиг финиша." if not ore_pos 
                        else "Не удалось найти путь к финишу."))
                    self.auto_running = False
                    break
        
        thread = threading.Thread(target=smart_task, daemon=True)
        thread.start()
    
    def stop_auto_traversal(self):
        self.auto_running = False
    
    def reset_maze(self):
        self.auto_running = False
        self.visited_cells.clear()
        
        # Сбрасываем лабиринт
        self.maze.initialize_maze(MineCellType.PATH)
        self.maze.cells[11][9].cell_type = MineCellType.FINISH
        self.create_interesting_maze()
        
        # Пересоздаем робота
        self.robot = RobotMiner(self.maze)
        
        self.update_info()
        self.draw_maze()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartMineMazeGUI(root)
    root.mainloop()
