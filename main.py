import tkinter as tk
import os
import openai
import json


openai.api_key = os.getenv("OPENAI_API_KEY")


class ChessGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChessGPT")

        # 메인 프레임 추가
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(side=tk.LEFT, padx=10)

        # 체스판의 크기와 색상 설정
        self.tile_size = 60
        self.colors = ["#8B4513", "#FFD700"]

        # 체스판 캔버스 프레임에 추가
        self.canvas = tk.Canvas(self.main_frame, width=8*self.tile_size, height=8*self.tile_size)
        self.canvas.pack(pady=20)

        for row in range(8):
            for col in range(8):
                color = self.colors[(row + col) % 2]
                self.canvas.create_rectangle(col*self.tile_size, row*self.tile_size,
                                             (col+1)*self.tile_size, (row+1)*self.tile_size,
                                             fill=color)
                position = f"{chr(97 + col)}{8 - row}"
                # 위치를 각 모서리에 표시
                self.canvas.create_text(col*self.tile_size + 2, row*self.tile_size, anchor="nw", text=position, fill="#C58E0A")


        # 이벤트 연결
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # 히스토리 영역 추가
        self.history_frame = tk.Frame(self)
        self.history_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_text = tk.Text(self.history_frame, wrap=tk.WORD, width=40)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        self.history_text.insert(tk.END, "Game History:\n\n")
        self.history_text.config(state=tk.DISABLED)  # 텍스트 위젯을 읽기 전용으로 만듭니다.

        # 기본적인 체스판 상태 (일단 폰만 사용). 위치는 체스기보법으로.
        self.pieces = {}

        # 체스판 초기화
        self.setup_board()

        self.print_board_status()

        self.openai_messages = [
            {"role": "system", "content": "You are playing chess with me. I play white and you play black. Response in JSON format with 'status'(success or error), 'board_state'(EFN), 'computer_move', 'message'. The message should be friendly and funny, and the rest should be accurate."},
        ]


    def get_piece_color(self, piece):
        return 'white' if piece.isupper() else 'black'


    def setup_board(self):
        # 기물들의 초기 배치
        initial_setup = {
            'a1': 'R', 'b1': 'N', 'c1': 'B', 'd1': 'Q', 'e1': 'K', 'f1': 'B', 'g1': 'N', 'h1': 'R',
            'a2': 'P', 'b2': 'P', 'c2': 'P', 'd2': 'P', 'e2': 'P', 'f2': 'P', 'g2': 'P', 'h2': 'P',
            'a7': 'p', 'b7': 'p', 'c7': 'p', 'd7': 'p', 'e7': 'p', 'f7': 'p', 'g7': 'p', 'h7': 'p',
            'a8': 'r', 'b8': 'n', 'c8': 'b', 'd8': 'q', 'e8': 'k', 'f8': 'b', 'g8': 'n', 'h8': 'r'
        }

        self.piece_to_emoji = {
            'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
            'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
        }

        for position, piece in initial_setup.items():
            col = ord(position[0]) - 97
            row = 8 - int(position[1])
            color = self.get_piece_color(piece)
            emoji = self.piece_to_emoji[piece]
            self.pieces[position] = self.canvas.create_text((col+0.5)*self.tile_size, (row+0.5)*self.tile_size,
                                                            text=emoji, fill=color, font=("Arial", 36))


    def add_message_to_history(self, message):
        """히스토리에 메시지를 추가합니다."""
        self.history_text.config(state=tk.NORMAL)  # 텍스트 위젯의 상태를 편집 가능하게 변경합니다.
        self.history_text.insert(tk.END, message + "\n")
        self.history_text.see(tk.END)  # 텍스트 위젯의 스크롤을 마지막 움직임으로 이동합니다.
        self.history_text.config(state=tk.DISABLED)  # 다시 읽기 전용으로 변경합니다.


    def on_click(self, event):
        col = int(event.x // self.tile_size)
        row = int(event.y // self.tile_size)
        position = f"{chr(97 + col)}{8 - row}"
    
        if position in self.pieces:
            piece_symbol = self.canvas.itemcget(self.pieces[position], "text")  # 기물의 심볼을 가져옵니다.
            color = self.get_piece_color(piece_symbol)  # 기물의 색상을 확인합니다.
    
            print(f"Clicked on: {position} ({color})")
            self.selected_piece = position


    def on_drag(self, event):
        if self.selected_piece:
            print(f"Dragging")
            self.canvas.coords(self.pieces[self.selected_piece],
                               event.x, event.y)


    def get_computer_move(self, player_move):
        self.openai_messages.append({"role": "user", "content": player_move})
    
        valid_move = False
        max_attempts = 3  # 최대 3번의 재요청을 허용합니다.
        current_attempt = 0
    
        response_json = None
        while not valid_move and current_attempt < max_attempts:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.openai_messages
            )
            response_str = completion.choices[0].message.content
            print(response_str)
            self.openai_messages.append({"role": "assistant", "content": response_str})
    
            response_json = json.loads(response_str)

            if response_json['message'].strip('.!') in ['Your turn', 'Your move']:
                self.add_message_to_history("ChatGPT move:" + response_json['computer_move'])
                self.add_message_to_history(response_json['message'] + "\n")
            else:
                self.add_message_to_history(response_json['message'])
                self.add_message_to_history("ChatGPT move:" + response_json['computer_move'] + "\n")
    
            # 움직임이 검정색 기물에 해당하는지 확인
            start_position = response_json['computer_move'].split("-")[0][-2:]
            if start_position in self.pieces and self.get_piece_color(self.canvas.itemcget(self.pieces[start_position], "text")) == "black":
                valid_move = True
                current_attempt = 0
            else:
                # 잘못된 움직임에 대한 응답 처리
                self.openai_messages.append({"role": "user", "content": "You did wrong move. It's my piece."})
                self.add_message_to_history("(ChatGPT did wrong move. It's player's piece. Retrying...)")
                current_attempt += 1
    
        if not valid_move:
            # 최대 재요청 횟수를 초과한 경우, 추가적인 처리가 필요합니다 (예: 에러 메시지 표시).
            # 현재는 간단하게 None을 반환합니다.
            return None
    
        return response_json['computer_move']


    def move_piece(self, move):
        if len(move) == 6 and move[3] == '-':
            move = move[1:]
        start, end = move.split("-")
        #print(f"Moving piece from {start} to {end}")
        piece = self.pieces.pop(start)

        # 만약 end 위치에 기물이 이미 있다면, 그 기물을 제거합니다.
        if end in self.pieces:
            piece_to_remove = self.pieces[end]
            self.canvas.delete(piece_to_remove)
            del self.pieces[end]

        self.pieces[end] = piece

        col_end = ord(end[0]) - 97
        row_end = 8 - int(end[1])

        self.canvas.coords(piece, col_end*self.tile_size + self.tile_size / 2, row_end*self.tile_size + self.tile_size / 2)


    def on_release(self, event):
        if self.selected_piece:
            col = round((event.x - self.tile_size/2) / self.tile_size)
            row = round((event.y - self.tile_size/2) / self.tile_size)
            end_position = f"{chr(97 + col)}{8 - row}"
            print(f"Released piece on {end_position}")
    
            # 움직임의 시작 셀과 릴리스한 셀의 위치가 같은 경우
            if self.selected_piece == end_position:
                self.place_piece_at_center(self.selected_piece, end_position)
                self.selected_piece = None
                return  # 릴리스 처리 종료, 다시 드래그할 수 있도록 함
        
            # 움직임 저장
            player_move = f"{self.selected_piece}-{end_position}"
            self.move_piece(player_move)
            self.add_message_to_history(f"Player move: {player_move}\n")
    
            # 컴퓨터의 움직임 처리
            computer_move = self.get_computer_move(player_move)
            if computer_move:
                start, end = computer_move.split("-")
                if start in self.pieces:
                    print(f"ChatGPT move: {computer_move}")
                    self.move_piece(computer_move)
    
            self.selected_piece = None


    def place_piece_at_center(self, piece_position, canvas_position):
        col = ord(canvas_position[0]) - 97
        row = 8 - int(canvas_position[1])
        center_x = (col + 0.5) * self.tile_size
        center_y = (row + 0.5) * self.tile_size
        self.canvas.coords(self.pieces[piece_position], center_x, center_y)


    def print_board_status(self):
        print("Board status:")
        for pos, piece_id in self.pieces.items():
            piece_symbol = self.canvas.itemcget(piece_id, "text")  # Canvas에서 기물의 심볼을 가져옵니다.
            color = self.get_piece_color(piece_symbol)  # 기물의 색상을 확인합니다.
            print(f"Piece at {pos} is {color} ({piece_symbol})")


if __name__ == "__main__":
    game = ChessGame()
    game.mainloop()
