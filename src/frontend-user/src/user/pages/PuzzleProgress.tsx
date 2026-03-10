/**
 * 残局挑战进度页面
 * 
 * 功能：
 * - 总通关数展示
 * - 难度进度
 * - 星级统计
 * - 排行榜
 */
import React, { useState, useEffect } from 'react'
import { api } from '@/services/api'

interface UserStatistics {
  total_completed: number
  total_attempts: number
  max_difficulty_passed: number
  total_stars: number
  stars_1: number
  stars_2: number
  stars_3: number
  ranking_points: number
  completion_rate: number
  difficulty_stats: Record<string, number>
}

interface LeaderboardEntry {
  rank: number
  user_id: number
  username: string
  ranking_points: number
  total_completed: number
  max_difficulty_passed: number
  total_stars: number
}

export const PuzzleProgress: React.FC = () => {
  const [statistics, setStatistics] = useState<UserStatistics | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [userRank, setUserRank] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [statsResponse, leaderboardResponse] = await Promise.all([
        api.get('/api/v1/puzzles/progress/'),
        api.get('/api/v1/puzzles/leaderboard/?limit=10'),
      ])

      if (statsResponse.data.success) {
        setStatistics(statsResponse.data.data)
      }

      if (leaderboardResponse.data.success) {
        setLeaderboard(leaderboardResponse.data.data.leaderboard)
        setUserRank(leaderboardResponse.data.data.user_rank)
      }
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const renderStars = (count: number, color: string) => {
    return (
      <div className="flex gap-1">
        {Array.from({ length: count }).map((_, i) => (
          <svg
            key={i}
            className={`w-5 h-5 ${color} fill-current`}
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">我的进度</h1>
        <p className="text-gray-600">查看你的残局挑战进度和排名</p>
      </div>

      {statistics && (
        <>
          {/* 统计概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {/* 总通关数 */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">总通关数</p>
              <p className="text-4xl font-bold text-red-600">{statistics.total_completed}</p>
              <p className="text-xs text-gray-400 mt-2">共 {statistics.total_attempts} 次挑战</p>
            </div>

            {/* 最高难度 */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">最高通过难度</p>
              <p className="text-4xl font-bold text-yellow-600">{statistics.max_difficulty_passed}星</p>
              <p className="text-xs text-gray-400 mt-2">继续挑战更高难度</p>
            </div>

            {/* 总星级 */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">总星级</p>
              <p className="text-4xl font-bold text-orange-600">{statistics.total_stars}</p>
              <div className="flex justify-center mt-2">
                {renderStars(Math.min(5, Math.floor(statistics.total_stars / 10)), 'text-orange-400')}
              </div>
            </div>

            {/* 排名积分 */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">排名积分</p>
              <p className="text-4xl font-bold text-blue-600">{statistics.ranking_points}</p>
              <p className="text-xs text-gray-400 mt-2">
                {userRank ? `第${userRank.rank}名` : '暂无排名'}
              </p>
            </div>
          </div>

          {/* 星级分布 */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">星级分布</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  {renderStars(1, 'text-yellow-400')}
                </div>
                <p className="text-2xl font-bold text-gray-900">{statistics.stars_1}</p>
                <p className="text-sm text-gray-500">1 星通关</p>
              </div>
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  {renderStars(2, 'text-yellow-400')}
                </div>
                <p className="text-2xl font-bold text-gray-900">{statistics.stars_2}</p>
                <p className="text-sm text-gray-500">2 星通关</p>
              </div>
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  {renderStars(3, 'text-yellow-400')}
                </div>
                <p className="text-2xl font-bold text-gray-900">{statistics.stars_3}</p>
                <p className="text-sm text-gray-500">3 星通关</p>
              </div>
            </div>
          </div>

          {/* 难度进度 */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">难度进度</h2>
            <div className="space-y-3">
              {['入门', '进阶', '高手', '大师'].map((level, idx) => {
                const start = idx * 3 + 1
                const end = start + 2
                const completed = Object.entries(statistics.difficulty_stats)
                  .filter(([diff]) => {
                    const d = parseInt(diff)
                    return d >= start && d <= end
                  })
                  .reduce((sum, [, count]) => sum + count, 0)
                
                const progress = (completed / 10) * 100
                
                return (
                  <div key={level} className="flex items-center gap-4">
                    <span className="w-16 text-sm text-gray-600">{level}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className={`h-4 rounded-full transition-all ${
                          idx === 0 ? 'bg-green-500' :
                          idx === 1 ? 'bg-yellow-500' :
                          idx === 2 ? 'bg-orange-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-20 text-right">
                      {completed} / 10
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}

      {/* 排行榜 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🏆 排行榜 Top 10</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">排名</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">用户</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-gray-600">通关数</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-gray-600">最高难度</th>
                <th className="text-center py-3 px-4 text-sm font-semibold text-gray-600">总星级</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600">积分</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry) => (
                <tr
                  key={entry.user_id}
                  className={`border-b border-gray-100 ${
                    entry.rank === 1 ? 'bg-yellow-50' :
                    entry.rank === 2 ? 'bg-gray-50' :
                    entry.rank === 3 ? 'bg-orange-50' : ''
                  }`}
                >
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold ${
                      entry.rank === 1 ? 'bg-yellow-400 text-white' :
                      entry.rank === 2 ? 'bg-gray-400 text-white' :
                      entry.rank === 3 ? 'bg-orange-400 text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {entry.rank}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-900 font-medium">{entry.username}</td>
                  <td className="py-3 px-4 text-center text-gray-700">{entry.total_completed}</td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-yellow-600 font-medium">{entry.max_difficulty_passed}星</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    {renderStars(Math.min(5, Math.floor(entry.total_stars / 10)), 'text-yellow-400')}
                  </td>
                  <td className="py-3 px-4 text-right text-red-600 font-bold">{entry.ranking_points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {userRank && (
          <div className="mt-4 pt-4 border-t border-gray-200 text-center text-sm text-gray-600">
            你的排名：第 <span className="font-bold text-red-600">{userRank.rank}</span> 名 · 
            积分：<span className="font-bold text-red-600">{userRank.ranking_points}</span>
          </div>
        )}
      </div>
    </div>
  )
}
