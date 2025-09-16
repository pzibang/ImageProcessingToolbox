import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageCutter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图片切割工具")
        self.root.geometry("1200x800")
        
        # 变量初始化
        self.template_image = None
        self.template_path = ""
        self.cut_line = None
        self.keep_side = None  # 保留的区域
        self.target_size = None
        self.display_image_obj = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制面板
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 选择模板图片按钮
        self.select_btn = tk.Button(control_frame, text="选择模板图片", command=self.select_template)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # 画线按钮
        self.draw_btn = tk.Button(control_frame, text="画切割线", command=self.draw_line, state=tk.DISABLED)
        self.draw_btn.pack(side=tk.LEFT, padx=5)
        
        # 选择保留区域按钮
        self.keep_btn = tk.Button(control_frame, text="选择保留区域", command=self.select_keep_area, state=tk.DISABLED)
        self.keep_btn.pack(side=tk.LEFT, padx=5)
        
        # 处理文件夹按钮
        self.process_btn = tk.Button(control_frame, text="处理文件夹", command=self.process_folder, state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        self.reset_btn = tk.Button(control_frame, text="重置", command=self.reset)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = tk.Label(control_frame, text="请选择模板图片")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 图像显示区域
        self.image_frame = tk.Frame(main_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.image_frame, bg='white', cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.drawing = False
        self.selecting_area = False
        self.start_x = None
        self.start_y = None
    
    def select_template(self):
        file_path = filedialog.askopenfilename(
            title="选择模板图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            self.template_path = file_path
            self.template_image = cv2.imread(file_path)
            if self.template_image is not None:
                self.target_size = self.template_image.shape[:2]  # (height, width)
                self.display_image(self.template_image)
                self.draw_btn.config(state=tk.NORMAL)
                self.status_label.config(text="模板已加载，请画切割线")
            else:
                messagebox.showerror("错误", "无法读取图片文件")
    
    def display_image(self, image):
        # 转换BGR到RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 调整图像大小以适应画布
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # 计算缩放比例
            h, w = image.shape[:2]
            scale = min(canvas_width / w, canvas_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            # 缩放图像
            resized_image = cv2.resize(image_rgb, (new_w, new_h))
            
            # 转换为PIL图像并显示
            pil_image = Image.fromarray(resized_image)
            self.tk_image = ImageTk.PhotoImage(pil_image)
            
            self.canvas.delete("all")
            self.canvas.create_image(canvas_width//2, canvas_height//2, 
                                   anchor=tk.CENTER, image=self.tk_image)
            
            # 保存显示信息用于坐标转换
            self.display_image_obj = {
                'scale': scale,
                'offset_x': (canvas_width - new_w) / 2,
                'offset_y': (canvas_height - new_h) / 2,
                'canvas_width': canvas_width,
                'canvas_height': canvas_height,
                'img_width': w,
                'img_height': h
            }
            
            # 如果存在切割线，重新绘制
            if self.cut_line:
                self.draw_existing_line()
    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """将画布坐标转换为图像坐标"""
        if not self.display_image_obj:
            return 0, 0
        
        img_x = max(0, min(self.display_image_obj['img_width'], 
                          (canvas_x - self.display_image_obj['offset_x']) / self.display_image_obj['scale']))
        img_y = max(0, min(self.display_image_obj['img_height'], 
                          (canvas_y - self.display_image_obj['offset_y']) / self.display_image_obj['scale']))
        return img_x, img_y
    
    def image_to_canvas_coords(self, img_x, img_y):
        """将图像坐标转换为画布坐标"""
        if not self.display_image_obj:
            return 0, 0
        
        canvas_x = img_x * self.display_image_obj['scale'] + self.display_image_obj['offset_x']
        canvas_y = img_y * self.display_image_obj['scale'] + self.display_image_obj['offset_y']
        return canvas_x, canvas_y
    
    def draw_existing_line(self):
        if self.cut_line and self.display_image_obj:
            x1, y1, x2, y2 = self.cut_line
            
            # 转换坐标到画布坐标系
            cx1, cy1 = self.image_to_canvas_coords(x1, y1)
            cx2, cy2 = self.image_to_canvas_coords(x2, y2)
            
            self.canvas.create_line(cx1, cy1, cx2, cy2, fill="red", width=2, tags="cut_line")
    
    def on_click(self, event):
        if self.template_image is None:
            return
            
        if self.drawing:
            # 正在画线
            self.start_x, self.start_y = event.x, event.y
        elif self.selecting_area:
            # 正在选择保留区域
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            self.determine_keep_side(img_x, img_y)
        
    def on_drag(self, event):
        if self.drawing and self.start_x is not None:
            self.canvas.delete("temp_line")
            self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, 
                                  fill="red", width=2, tags="temp_line")
    
    def on_release(self, event):
        if self.drawing and self.start_x is not None:
            self.drawing = False
            
            # 获取画布上的坐标并转换为图像坐标
            start_img_x, start_img_y = self.canvas_to_image_coords(self.start_x, self.start_y)
            end_img_x, end_img_y = self.canvas_to_image_coords(event.x, event.y)
            
            # 自动拟合到图像边缘
            fitted_line = self.fit_line_to_edges(start_img_x, start_img_y, end_img_x, end_img_y)
            
            if fitted_line:
                self.cut_line = fitted_line
                
                # 清除临时线，绘制永久线
                self.canvas.delete("temp_line")
                self.canvas.delete("cut_line")
                self.draw_existing_line()
                
                self.keep_btn.config(state=tk.NORMAL)
                self.status_label.config(text="✅ 切割线已绘制完成，请点击'选择保留区域'按钮")
                
                # 清除操作提示
                self.canvas.delete("hint")

    def fit_line_to_edges(self, x1, y1, x2, y2):
        """将直线拟合到图像边缘，并确保与图像边缘平行或垂直"""
        if self.template_image is None:
            return None
            
        h, w = self.template_image.shape[:2]
        
        # 计算直线角度（相对于水平方向）
        dx = x2 - x1
        dy = y2 - y1
        
        # 如果直线太短，无法准确计算角度，返回原线
        if abs(dx) < 5 and abs(dy) < 5:
            return (x1, y1, x2, y2)
        
        # 计算角度（弧度）并转换为0-180度范围
        angle = np.arctan2(dy, dx)
        angle_deg = np.degrees(angle) % 180
        
        # 定义角度容差（10度）
        angle_tolerance = 10
        
        # 检查是否接近水平（0°或180°）或垂直（90°）
        is_horizontal = (angle_deg < angle_tolerance or angle_deg > 180 - angle_tolerance)
        is_vertical = (abs(angle_deg - 90) < angle_tolerance)
        
        # 如果既不是水平也不是垂直，强制修正为最接近的水平或垂直方向
        if not (is_horizontal or is_vertical):
            # 计算到水平和垂直方向的角度差
            to_horizontal = min(angle_deg, 180 - angle_deg)
            to_vertical = abs(angle_deg - 90)
            
            # 选择最接近的方向
            if to_horizontal <= to_vertical:
                # 修正为水平方向
                avg_y = (y1 + y2) / 2
                return (0, avg_y, w, avg_y)
            else:
                # 修正为垂直方向
                avg_x = (x1 + x2) / 2
                return (avg_x, 0, avg_x, h)
        
        # 对于已经是水平或垂直的直线，延长到边缘
        if is_vertical:  # 垂直线
            avg_x = (x1 + x2) / 2
            return (avg_x, 0, avg_x, h)
        else:  # 水平线
            avg_y = (y1 + y2) / 2
            return (0, avg_y, w, avg_y)
        
        # 计算与四个边的交点
        intersections = []
        
        # 与上边缘的交点 (y=0)
        if slope != 0:
            x_top = -intercept / slope
            if 0 <= x_top <= w:
                intersections.append((x_top, 0))
        
        # 与下边缘的交点 (y=h)
        x_bottom = (h - intercept) / slope
        if 0 <= x_bottom <= w:
            intersections.append((x_bottom, h))
        
        # 与左边缘的交点 (x=0)
        y_left = intercept
        if 0 <= y_left <= h:
            intersections.append((0, y_left))
        
        # 与右边缘的交点 (x=w)
        y_right = slope * w + intercept
        if 0 <= y_right <= h:
            intersections.append((w, y_right))
        
        # 取两个最远的交点
        if len(intersections) >= 2:
            # 计算所有点对之间的距离
            max_distance = 0
            best_pair = None
            
            for i in range(len(intersections)):
                for j in range(i+1, len(intersections)):
                    dist = np.sqrt((intersections[i][0]-intersections[j][0])**2 + 
                                 (intersections[i][1]-intersections[j][1])**2)
                    if dist > max_distance:
                        max_distance = dist
                        best_pair = (intersections[i], intersections[j])
            
            if best_pair:
                return (best_pair[0][0], best_pair[0][1], best_pair[1][0], best_pair[1][1])
        
        return (x1, y1, x2, y2)  # 如果无法拟合，返回原线

    def draw_line(self):
        self.drawing = True
        self.selecting_area = False
        self.status_label.config(text="✏️ 请在图像上拖动鼠标绘制切割线（程序会自动延长到边缘）")
        
        # 清除之前的提示
        self.canvas.delete("hint")
        # 添加操作提示
        if self.display_image_obj:
            self.canvas.create_text(self.display_image_obj['canvas_width']//2, 
                                  self.display_image_obj['canvas_height'] - 20, 
                                  anchor="center", text="拖动鼠标绘制切割线", 
                                  fill="red", font=("Arial", 10, "bold"), tags="hint")

    def select_keep_area(self):
        if not self.cut_line:
            messagebox.showwarning("警告", "请先绘制切割线")
            return
        
        self.drawing = False
        self.selecting_area = True
        self.status_label.config(text="🖱️ 请在图像上点击选择要保留的区域（左侧或右侧）")
        
        # 清除之前的提示
        self.canvas.delete("hint")
        # 添加操作提示
        if self.display_image_obj:
            self.canvas.create_text(self.display_image_obj['canvas_width']//2, 
                                  self.display_image_obj['canvas_height'] - 20, 
                                  anchor="center", text="点击左侧或右侧选择保留区域", 
                                  fill="red", font=("Arial", 10, "bold"), tags="hint")

    def determine_keep_side(self, click_x, click_y):
        """根据点击位置确定要保留的区域"""
        if not self.cut_line:
            return
        
        x1, y1, x2, y2 = self.cut_line
        
        # 计算直线方程: Ax + By + C = 0
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        # 计算点击位置相对于直线的位置
        distance = A * click_x + B * click_y + C
        
        # 确定保留的区域
        if distance <= 0:
            self.keep_side = "left"
            side_text = "左侧"
        else:
            self.keep_side = "right"
            side_text = "右侧"
        
        self.selecting_area = False
        self.process_btn.config(state=tk.NORMAL)
        
        # 显示更详细的提示信息
        self.status_label.config(text=f"✅ 已选择保留{side_text}区域，点击'处理文件夹'按钮开始批量处理")
        
        # 在画布上显示选择结果
        self.canvas.delete("selection")
        if self.display_image_obj:
            # 在整个画布上显示半透明区域表示保留的部分
            if self.keep_side == "left":
                self.canvas.create_rectangle(0, 0, self.display_image_obj['canvas_width'], 
                                           self.display_image_obj['canvas_height'], 
                                           fill="green", stipple="gray25", 
                                           outline="", tags="selection")
            else:
                self.canvas.create_rectangle(0, 0, self.display_image_obj['canvas_width'], 
                                           self.display_image_obj['canvas_height'], 
                                           fill="blue", stipple="gray25", 
                                           outline="", tags="selection")
            
            # 添加文字提示
            self.canvas.create_text(10, 10, anchor="nw", text=f"保留{side_text}", 
                                  fill="white", font=("Arial", 12, "bold"), tags="selection")

    def process_single_image(self, image_path):
        """处理单张图片"""
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                print(f"无法读取图片: {image_path}")
                return False
            
            # 检查图片尺寸是否与模板一致
            if image.shape[:2] != self.template_image.shape[:2]:
                # 调整到模板尺寸
                image = cv2.resize(image, (self.template_image.shape[1], self.template_image.shape[0]))
            
            # 应用切割
            result_image = self.apply_cut(image)
            
            if result_image is None:
                return False
            
            # 保存结果（覆盖原文件）
            cv2.imwrite(image_path, result_image)
            return True
            
        except Exception as e:
            print(f"处理图片 {image_path} 时出错: {e}")
            return False

    def apply_cut(self, image):
        """应用切割操作"""
        if not all([self.cut_line is not None, self.keep_side is not None]):
            return None
        
        h, w = image.shape[:2]
        x1, y1, x2, y2 = self.cut_line
        
        # 创建掩码
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # 计算直线方程: Ax + By + C = 0
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        # 为每个像素计算到直线的距离
        for y in range(h):
            for x in range(w):
                distance = A * x + B * y + C
                if self.keep_side == "left":
                    if distance <= 0:  # 保留左侧
                        mask[y, x] = 255
                else:  # 保留右侧
                    if distance >= 0:
                        mask[y, x] = 255
        
        # 应用掩码
        result = cv2.bitwise_and(image, image, mask=mask)
        
        # 找到保留区域的最小边界矩形
        coords = cv2.findNonZero(mask)
        if coords is not None:
            x, y, w_rect, h_rect = cv2.boundingRect(coords)
            # 裁剪到最小矩形区域
            result = result[y:y+h_rect, x:x+w_rect]
        
        return result

    def process_folder(self):
        if not all([self.template_image is not None, self.cut_line is not None, self.keep_side is not None]):
            messagebox.showwarning("警告", "请先完成所有设置步骤：1.选择模板图片 2.绘制切割线 3.选择保留区域")
            return
        
        folder_path = filedialog.askdirectory(title="选择要处理的图片文件夹")
        if not folder_path:
            return
        
        # 获取所有图片文件（包括子文件夹）
        image_files = []
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # 递归遍历所有子文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in supported_extensions:
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            messagebox.showinfo("信息", "文件夹及其子文件夹中没有找到图片文件")
            return
        
        # 显示处理进度
        self.status_label.config(text=f"🔄 正在处理 {len(image_files)} 张图片（包含子文件夹）...")
        self.root.update()
        
        # 处理图片
        processed_count = 0
        for i, image_path in enumerate(image_files):
            try:
                success = self.process_single_image(image_path)
                if success:
                    processed_count += 1
                # 更新进度
                self.status_label.config(text=f"🔄 正在处理 ({i+1}/{len(image_files)}) - {os.path.basename(image_path)}")
                self.root.update()
            except Exception as e:
                print(f"处理图片 {image_path} 时出错: {e}")
        
        messagebox.showinfo("完成", f"✅ 处理完成！成功处理了 {processed_count}/{len(image_files)} 张图片（包含所有子文件夹）")
        self.status_label.config(text=f"✅ 批量处理完成，共处理 {processed_count} 张图片（包含子文件夹）")

    def reset(self):
        """重置所有设置"""
        self.cut_line = None
        self.keep_side = None
        self.drawing = False
        self.selecting_area = False
        self.canvas.delete("all")
        
        if self.template_image is not None:
            self.display_image(self.template_image)
        
        self.draw_btn.config(state=tk.NORMAL)
        self.keep_btn.config(state=tk.DISABLED)
        self.process_btn.config(state=tk.DISABLED)
        self.status_label.config(text="🔄 已重置，请重新绘制切割线")
        
        # 清除所有提示
        self.canvas.delete("hint")
    
    def run(self):
        # 定期更新图像显示
        def update_display():
            if self.template_image is not None:
                self.display_image(self.template_image)
            self.root.after(100, update_display)
        
        self.root.after(100, update_display)
        self.root.mainloop()

if __name__ == "__main__":
    app = ImageCutter()
    app.run()