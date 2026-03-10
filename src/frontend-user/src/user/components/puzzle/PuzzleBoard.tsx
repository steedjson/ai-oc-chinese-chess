/**
 * 残局棋盘组件
 * 
 * 功能：
 * - FEN 解析与渲染
 * - 棋子点击交互
 * - 走棋验证提示
 */
import React, { useState, useMemo, useCallback } from 'react'

interface PuzzleBoardProps {
  fen: string
  onMove: (from: string, to: string, piece: string) => void
  disabled?: boolean
}

interface Piece {
  type: string
  color: 'red' | 'black'
  position: string
}

interface BoardState {
  squares: Record<string, Piece>
  turn: 'red' | 'black'
}

// FEN 解析
const parseFen = (fen: string): BoardState => {
  const parts = fen.split(' ')
  const boardStr = parts[0]
  const turn = parts[1] === 'w' ? 'red' : 'black'
  
  const squares: Record<string, Piece> = {}
  const rows = boardStr.split('/')
  
  rows.forEach((rowStr, rowIndex) => {
    const row = 9 - rowIndex // FEN 从第 9 行开始
    let colIndex = 0
    
    for (const char of rowStr) {
      if (/\d/.test(char)) {
        colIndex += parseInt(char)
      } else {
        const col = String.fromCharCode(97 + colIndex) // a, b, c...
        const position = `${col}${row}`
        const color = char === char.toUpperCase() ? 'red' : 'black'
        const type = char.toUpperCase()
        
        squares[position] = { type, color, position }
        colIndex++
      }
    }
  })
  
  return { squares, turn }
}

// 棋子中文显示
const getPieceText = (type: string, color: 'red' | 'black'): string => {
  const pieces: Record<string, { red: string, black: string }> = {
    'K': { red: '帅', black: '将' },
    'A': { red: '仕', black: '士' },
    'B': { red: '相', black: '象' },
    'N': { red: '马', black: '马' },
    'R': { red: '车', black: '车' },
    'C': { red: '炮', black: '炮' },
    'P': { red: '兵', black: '卒' },
  }
  
  return pieces[type]?.[color] || ''
}

// 坐标转换
const positionToCoords = (position: string): { x: number, y: number } => {
  const col = position.charCodeAt(0) - 97 // a=0, b=1...
  const row = parseInt(position[1]) - 1  // 1=0, 2=1...
  
  return {
    x: 50 + col * 50,
    y: 450 - row * 50,
  }
}

export const PuzzleBoard: React.FC<PuzzleBoardProps> = ({
  fen,
  onMove,
  disabled = false,
}) => {
  const boardState = useMemo(() => parseFen(fen), [fen])
  const [selectedPos, setSelectedPos] = useState<string | null>(null)

  const handleClick = useCallback((position: string) => {
    if (disabled) return
    
    const piece = boardState.squares[position]
    
    if (selectedPos) {
      // 已选中棋子，尝试移动
      if (selectedPos !== position) {
        // 移动到目标位置
        const selectedPiece = boardState.squares[selectedPos]
        if (selectedPiece) {
          onMove(selectedPos, position, selectedPiece.type)
          setSelectedPos(null)
        }
      } else {
        // 取消选中
        setSelectedPos(null)
      }
    } else {
      // 未选中，选择棋子（只能选红方）
      if (piece && piece.color === 'red') {
        setSelectedPos(position)
      }
    }
  }, [selectedPos, boardState, onMove, disabled])

  // 生成棋盘网格
  const renderGrid = () => {
    const lines = []
    
    // 横线 (10 条)
    for (let i = 0; i < 10; i++) {
      const y = 50 + i * 50
      lines.push(
        <line
          key={`h-${i}`}
          x1="50"
          y1={y}
          x2="450"
          y2={y}
          stroke="#000"
          strokeWidth="2"
        />
      )
    }
    
    // 竖线 (9 条，中间断开)
    for (let i = 0; i < 9; i++) {
      const x = 50 + i * 50
      
      // 上半部分 (0-4 行)
      lines.push(
        <line
          key={`v-top-${i}`}
          x1={x}
          y1="50"
          x2={x}
          y2="250"
          stroke="#000"
          strokeWidth="2"
        />
      )
      
      // 下半部分 (5-9 行)
      lines.push(
        <line
          key={`v-bottom-${i}`}
          x1={x}
          y1="300"
          x2={x}
          y2="450"
          stroke="#000"
          strokeWidth="2"
        />
      )
    }
    
    // 九宫格斜线
    lines.push(
      <line key="palace-1" x1="200" y1="50" x2="300" y2="150" stroke="#000" strokeWidth="2" />,
      <line key="palace-2" x1="300" y1="50" x2="200" y2="150" stroke="#000" strokeWidth="2" />,
      <line key="palace-3" x1="200" y1="350" x2="300" y2="450" stroke="#000" strokeWidth="2" />,
      <line key="palace-4" x1="300" y1="350" x2="200" y2="450" stroke="#000" strokeWidth="2" />
    )
    
    // 河界文字
    lines.push(
      <text key="river-1" x="150" y="285" fontSize="24" fill="#000" textAnchor="middle">楚 河</text>,
      <text key="river-2" x="350" y="285" fontSize="24" fill="#000" textAnchor="middle">汉 界</text>
    )
    
    return <g className="grid">{lines}</g>
  }

  // 生成棋子
  const renderPieces = () => {
    return Object.values(boardState.squares).map((piece) => {
      const { x, y } = positionToCoords(piece.position)
      const isSelected = selectedPos === piece.position
      
      return (
        <g
          key={piece.position}
          onClick={() => handleClick(piece.position)}
          className={disabled ? '' : 'cursor-pointer hover:opacity-80'}
        >
          {/* 棋子背景 */}
          <circle
            cx={x}
            cy={y}
            r="22"
            fill="#f5deb3"
            stroke={isSelected ? '#ff0000' : '#8b4513'}
            strokeWidth={isSelected ? 4 : 2}
          />
          
          {/* 棋子文字 */}
          <text
            x={x}
            y={y + 8}
            fontSize="20"
            fontWeight="bold"
            fill={piece.color === 'red' ? '#c00' : '#000'}
            textAnchor="middle"
            className="select-none"
          >
            {getPieceText(piece.type, piece.color)}
          </text>
        </g>
      )
    })
  }

  return (
    <div className="relative">
      <svg
        viewBox="0 0 500 500"
        className="w-full max-w-[500px] bg-[#f5deb3] rounded-lg shadow-lg"
      >
        {/* 棋盘网格 */}
        {renderGrid()}
        
        {/* 棋子 */}
        {renderPieces()}
      </svg>
      
      {disabled && (
        <div className="absolute inset-0 bg-black bg-opacity-10 rounded-lg flex items-center justify-center">
          <div className="text-white text-lg font-bold">挑战已完成</div>
        </div>
      )}
    </div>
  )
}
