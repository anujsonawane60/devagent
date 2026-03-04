import { User, ApiResponse } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api'

export async function fetchUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE}/users`)
  if (!response.ok) {
    throw new Error('Failed to fetch users')
  }
  return response.json()
}

export async function fetchUserById(id: number): Promise<User> {
  const response = await fetch(`${API_BASE}/users/${id}`)
  if (!response.ok) {
    throw new Error(`User ${id} not found`)
  }
  return response.json()
}

export async function createUser(data: Partial<User>): Promise<User> {
  const response = await fetch(`${API_BASE}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return response.json()
}

export function buildQueryString(params: Record<string, string>): string {
  return new URLSearchParams(params).toString()
}

export const formatApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}
