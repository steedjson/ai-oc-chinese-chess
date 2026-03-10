/**
 * 残局挑战界面
 * 
 * 功能：
 * - 棋盘展示
 * - 走棋验证
 * - 步数计数器
 * - 计时器
 * - 提示功能
 * - 完成界面
 */
import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/services/api'
import { PuzzleBoard } from '../components/puzzle/PuzzleBoard'
import { PuzzleHint } from '../components/puzzle/PuzzleHint'

interface Attempt {
  attempt_id: string
  puzzle_id: string
  fen_current: string
  status: string
  current_move_index: number
  move_limit?: number
  time_limit?: number
  started_at: string
}

interface MoveResult {
  correct: boolean
  message: string
  fen_current: string
  current_move_index: number
  remaining_moves: number
  is_complete: boolean
  stars?: number
  points_earned?: number
}

export const PuzzleChallenge: React.FC = () => {
  const { puzzleId } = useParams<{ puzzleId: string }>()
  const navigate = useNavigate()
  
  const [attempt, setAttempt] = useState<Attempt | null>(null)
  const [fen, setFen] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null)
  const [showHint, setShowHint] = useState(false)
  const [hint, setHint] = useState<string>('')
  const [timeElapsed, setTimeElapsed] = useState(0)
  const [completed, setCompleted] = useState(false)
  const [result, setResult] = useState<{ stars: number, points: number, moves: number } | null>(null)

  // 启动计时器
  useEffect(() => {
    if (attempt && !completed) {
      const timer = setInterval(() => {
        setTimeElapsed(prev => prev + 1)
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [attempt, completed])

  // 加载挑战
  useEffect(() => {
    startChallenge()
  }, [puzzleId])

  const startChallenge = async () => {
    if (!puzzleId) return
    
    try {
      const response = await api.post(`/api/v1/puzzles/${puzzleId}/attempt/`)
      if (response.data.success) {
        setAttempt(response.data.data)
        setFen(response.data.data.fen_current)
      }
    } catch (error) {
      console.error('创建挑战失败:', error)
      setMessage({ type: 'error', text: '创建挑战失败，请重试' })
    } finally {
      setLoading(false)
    }
  }

  const handleMove = useCallback(async (from: string, to: string, piece: string) => {
    if (!attempt || submitting || completed) return
    
    setSubmitting(true)
    setMessage(null)
    
    try {
      const response = await api.post(
        `/api/v1/puzzles/${puzzleId}/attempts/${attempt.attempt_id}/move/`,
        { from, to, piece }
      )
      
      if (response.data.success) {
        const data = response.data.data
        
        if (data.correct) {
          setFen(data.fen_current)
          setMessage({ type: 'success', text: data.message })
          
          if (data.is_complete) {
            setCompleted(true)
            setResult({
              stars: data.stars || 0,
              points: data.points_earned || 0,
              moves: data.current_move_index,
            })
          }
        } else {
          setMessage({ type: 'error', text: data.message })
        }
      }
    } catch (error: any) {
      console.error('提交走法失败:', error)
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error?.message || '提交走法失败' 
      })
    } finally {
      setSubmitting(false)
    }
  }, [attempt, submitting, completed, puzzleId])

  const handleShowHint = async () => {
    if (!puzzleId) return
    
    try {
      const response = await api.get(`/api/v1/puzzles/${puzzleId}/`)
      if (response.data.success) {
        setHint(response.data.data.hint || '暂无提示')
        setShowHint(true)
      }
    } catch (error) {
      console.error('获取提示失败:', error)
    }
  }

  const handleRestart = () => {
    setCompleted(false)
    setResult(null)
    setTimeElapsed(0)
    setMessage(null)
    setShowHint(false)
    startChallenge()
  }

  const handleBack = () => {
    navigate('/puzzles')
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const renderStars = (stars: number) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3].map((star) => (
          <svg
            key={star}
            className={`w-8 h-8 ${star <= stars ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
            viewBox="0 0 20 20"
          >
            <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
          </svg>
        ))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    )
  }

  if (!attempt) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600 mb-4">无法加载挑战</p>
          <button
            onClick={handleBack}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            返回
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 顶部信息栏 */}
      <div className="mb-6 flex items-center justify-between">
        <button
          onClick={handleBack}
          className="text-gray-600 hover:text-gray-900"
        >
          ← 返回
        </button>
        
        <div className="flex items-center gap-6">
          {/* 计时器 */}
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-lg font-mono text-gray-700">{formatTime(timeElapsed)}</span>
          </div>
          
          {/* 步数 */}
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span className="text-lg font-mono text-gray-700">
              步数：{attempt.current_move_index}{attempt.move_limit ? `/${attempt.move_limit}` : ''}
            </span>
          </div>
        </div>
        
        <button
          onClick={handleShowHint}
          className="px-4 py-2 text-yellow-600 border border-yellow-600 rounded-lg hover:bg-yellow-50"
        >
          💡 提示
        </button>
      </div>

      {/* 消息提示 */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-100 text-green-800' :
          message.type === 'error' ? 'bg-red-100 text-red-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {message.text}
        </div>
      )}

      {/* 提示框 */}
      {showHint && hint && (
        <PuzzleHint hint={hint} onClose={() => setShowHint(false)} />
      )}

      {/* 完成界面 */}
      {completed && result && (
        <div className="mb-6 p-6 bg-gradient-to-r from-yellow-100 to-orange-100 rounded-lg text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">🎉 挑战成功!</h2>
          <div className="flex items-center justify-center gap-4 mb-4">
            {renderStars(result.stars)}
          </div>
          <div className="flex items-center justify-center gap-8 text-gray-700">
            <div>
              <p className="text-sm text-gray-500">使用步数</p>
              <p className="text-xl font-bold">{result.moves}步</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">获得积分</p>
              <p className="text-xl font-bold text-red-600">+{result.points}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">用时</p>
              <p className="text-xl font-bold">{formatTime(timeElapsed)}</p>
            </div>
          </div>
          <div className="mt-6 flex items-center justify-center gap-4">
            <button
              onClick={handleRestart}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              再玩一次
            </button>
            <button
              onClick={handleBack}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              返回关卡列表
            </button>
          </div>
        </div>
      )}

      {/* 棋盘 */}
      <div className="flex items-start justify-center gap-8">
        <PuzzleBoard
          fen={fen}
          onMove={handleMove}
          disabled={submitting || completed}
        />
        
        {/* 侧边信息 */}
        <div className="w-64">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">挑战信息</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500">当前步骤</p>
                <p className="text-lg font-semibold text-gray-900">
                  {attempt.current_move_index} / {attempt.move_limit || '∞'}
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">状态</p>
                <p className={`text-lg font-semibold ${
                  completed ? 'text-green-600' : 'text-blue-600'
                }`}>
                  {completed ? '已完成' : '进行中'}
                </p>
              </div>
              
              <div className="pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500 mb-2">操作说明</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 点击棋子选中</li>
                  <li>• 点击目标位置走棋</li>
                  <li>• 绿色标记为正确走法</li>
                  <li>• 按解法顺序完成挑战</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
