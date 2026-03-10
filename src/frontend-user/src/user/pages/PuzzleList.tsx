/**
 * 残局挑战关卡列表页面
 * 
 * 功能：
 * - 关卡列表展示
 * - 难度筛选
 * - 星级显示
 * - 已通关标记
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/services/api'

interface Puzzle {
  id: string
  title: string
  description: string
  difficulty: number
  stars: number
  move_limit?: number
  time_limit?: number
  total_attempts: number
  total_completions: number
  completion_rate: number
  user_completed?: boolean
  user_stars?: number
}

interface Pagination {
  page: number
  page_size: number
  total_count: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export const PuzzleList: React.FC = () => {
  const navigate = useNavigate()
  const [puzzles, setPuzzles] = useState<Puzzle[]>([])
  const [pagination, setPagination] = useState<Pagination | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDifficulty, setSelectedDifficulty] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    loadPuzzles()
  }, [currentPage, selectedDifficulty])

  const loadPuzzles = async () => {
    setLoading(true)
    try {
      const params: any = {
        page: currentPage,
        page_size: 20,
      }
      if (selectedDifficulty) {
        params.difficulty = selectedDifficulty
      }

      const response = await api.get('/api/v1/puzzles/', { params })
      if (response.data.success) {
        setPuzzles(response.data.data.results)
        setPagination(response.data.data.pagination)
      }
    } catch (error) {
      console.error('加载关卡列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDifficultyFilter = (difficulty: number | null) => {
    setSelectedDifficulty(difficulty)
    setCurrentPage(1)
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const getDifficultyLabel = (difficulty: number) => {
    const labels: Record<number, string> = {
      1: '入门',
      2: '入门',
      3: '入门',
      4: '进阶',
      5: '进阶',
      6: '进阶',
      7: '高手',
      8: '高手',
      9: '大师',
      10: '大师',
    }
    return labels[difficulty] || ''
  }

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 3) return 'text-green-600 bg-green-100'
    if (difficulty <= 6) return 'text-yellow-600 bg-yellow-100'
    if (difficulty <= 8) return 'text-orange-600 bg-orange-100'
    return 'text-red-600 bg-red-100'
  }

  const renderStars = (stars: number, size: string = 'w-4 h-4') => {
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`${size} ${star <= stars ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
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

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">残局挑战</h1>
        <p className="text-gray-600">挑战经典残局，提升棋艺水平</p>
      </div>

      {/* 难度筛选 */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => handleDifficultyFilter(null)}
          className={`px-4 py-2 rounded-lg transition-colors ${
            selectedDifficulty === null
              ? 'bg-red-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          全部
        </button>
        {[1, 4, 7, 10].map((diff) => (
          <button
            key={diff}
            onClick={() => handleDifficultyFilter(diff)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedDifficulty === diff
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {getDifficultyLabel(diff)} ({diff}星)
          </button>
        ))}
      </div>

      {/* 关卡列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {puzzles.map((puzzle) => (
          <div
            key={puzzle.id}
            onClick={() => navigate(`/puzzles/${puzzle.id}`)}
            className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
          >
            {/* 关卡标题 */}
            <h3 className="text-xl font-bold text-gray-900 mb-2">{puzzle.title}</h3>
            
            {/* 关卡描述 */}
            <p className="text-gray-600 text-sm mb-4 line-clamp-2">{puzzle.description}</p>
            
            {/* 难度标签 */}
            <div className="flex items-center justify-between mb-4">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(puzzle.difficulty)}`}>
                {getDifficultyLabel(puzzle.difficulty)} · {puzzle.difficulty}星
              </span>
              {puzzle.user_completed && (
                <span className="text-green-600 text-sm font-medium">✓ 已通关</span>
              )}
            </div>
            
            {/* 星级显示 */}
            <div className="mb-4">
              {puzzle.user_completed ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">我的成绩:</span>
                  {renderStars(puzzle.user_stars || 0)}
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">推荐星级:</span>
                  {renderStars(puzzle.stars)}
                </div>
              )}
            </div>
            
            {/* 统计信息 */}
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>通关率：{puzzle.completion_rate.toFixed(1)}%</span>
              <span>挑战：{puzzle.total_attempts}次</span>
            </div>
            
            {/* 限制信息 */}
            {(puzzle.move_limit || puzzle.time_limit) && (
              <div className="mt-4 pt-4 border-t border-gray-200 flex gap-4 text-sm text-gray-500">
                {puzzle.move_limit && <span>限{puzzle.move_limit}步</span>}
                {puzzle.time_limit && <span>限时{Math.floor(puzzle.time_limit / 60)}分钟</span>}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 分页 */}
      {pagination && pagination.total_pages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={!pagination.has_prev}
            className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
          >
            上一页
          </button>
          
          <span className="px-4 py-2 text-gray-700">
            第 {pagination.page} / {pagination.num_pages} 页
          </span>
          
          <button
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={!pagination.has_next}
            className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}
