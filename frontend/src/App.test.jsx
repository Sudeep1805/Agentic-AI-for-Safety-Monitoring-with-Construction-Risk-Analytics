import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { request } from './api'

vi.mock('./api', () => ({
  fetchImage: vi.fn(() => Promise.resolve('blob:test-image')),
  request: vi.fn(),
  saveAuthToken: vi.fn(),
  clearAuthToken: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
  window.location.hash = ''
  request.mockImplementation((path) => {
    if (path === '/health/ready') return Promise.resolve({ status: 'ready' })
    if (path === '/api/auth/me') return Promise.reject(new Error('not signed in'))
    return Promise.resolve({ items: [], total: 0 })
  })
})

describe('workspace dashboard', () => {
  it('renders overview metrics and honest analysis status', async () => {
    render(<App />)
    expect((await screen.findAllByText('Your observation log starts here')).length).toBeGreaterThan(0)
    expect(screen.getByText('No analysis yet.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Site Risks/i })).toBeInTheDocument()
  })

  it('renders completed analysis results from the upload API', async () => {
    window.location.hash = 'risks'
    request.mockImplementation((path) => {
      if (path === '/health/ready') return Promise.resolve({ status: 'ready' })
      if (path === '/api/auth/me') return Promise.resolve({ id: '1', email: 'worker@example.com', full_name: 'Site Worker' })
      if (path === '/api/uploads') return Promise.resolve({
        items: [{
          id: 'upload-1',
          original_filename: 'site.jpg',
          content_type: 'image/jpeg',
          size_bytes: 100,
          width: 32,
          height: 24,
          created_at: '2026-10-17T12:00:00Z',
          image_url: '/api/uploads/upload-1/image',
          analysis_status: 'completed',
          analysis_message: 'YOLO detection completed.',
          detections: [{ class_id: 4, class_name: 'NO-Safety Vest', confidence: 0.81, bbox: [1, 2, 3, 4] }],
          risk_score: 25,
          risk_level: 'Medium',
          hazard_count: 1,
          hazards: [{ hazard: 'NO-Safety Vest', confidence: 0.81, penalty: 25, description: 'Possible PPE violation detected: NO-Safety Vest' }],
        }],
        total: 1,
      })
    })

    render(<App />)

    expect(await screen.findByText('Analysis completed')).toBeInTheDocument()
    expect(screen.getAllByText('25/100').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Medium').length).toBeGreaterThan(0)
    expect(screen.getAllByText('NO-Safety Vest').length).toBeGreaterThan(0)
    expect(screen.getAllByText('81.0%').length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Possible PPE violation detected: NO-Safety Vest/).length).toBeGreaterThan(0)
    expect(screen.queryByText('No AI analysis was performed.')).not.toBeInTheDocument()
    expect(screen.queryByText('Not assessed')).not.toBeInTheDocument()
  })

  it('shows a completed zero-hazard analysis without an unavailable message', async () => {
    window.location.hash = 'risks'
    request.mockImplementation((path) => {
      if (path === '/health/ready') return Promise.resolve({ status: 'ready' })
      if (path === '/api/auth/me') return Promise.reject(new Error('not signed in'))
      if (path === '/api/uploads') return Promise.resolve({
        items: [{
          id: 'upload-2',
          original_filename: 'clear-site.png',
          content_type: 'image/png',
          size_bytes: 100,
          width: 32,
          height: 24,
          created_at: '2026-10-17T12:00:00Z',
          image_url: '/api/uploads/upload-2/image',
          analysis_status: 'completed',
          analysis_message: 'YOLO detection completed. 0 object(s) detected.',
          detections: [],
          risk_score: 0,
          risk_level: 'Low',
          hazard_count: 0,
          hazards: [],
        }],
        total: 1,
      })
    })

    render(<App />)

    expect(await screen.findByText('No configured hazards detected in this image.')).toBeInTheDocument()
    expect(screen.getAllByText('0/100').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Low').length).toBeGreaterThan(0)
    expect(screen.queryByText('Analysis unavailable')).not.toBeInTheDocument()
    expect(screen.queryByText('Not assessed')).not.toBeInTheDocument()
  })

  it('navigates to placeholder modules through the hash sidebar', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('link', { name: /Projects/i }))
    expect((await screen.findAllByText('Projects')).length).toBeGreaterThan(0)
    expect(screen.getByText('SITE PORTFOLIO')).toBeInTheDocument()
    expect(screen.getByText('Manage construction sites and active operations.')).toBeInTheDocument()
    expect(screen.getByText('Greenfield Residential Construction')).toBeInTheDocument()
    expect(screen.getByText('Coimbatore, Tamil Nadu')).toBeInTheDocument()
    expect(screen.getByText('Smart Highway Infrastructure')).toBeInTheDocument()
    expect(screen.getByText('Salem, Tamil Nadu')).toBeInTheDocument()
    expect(screen.getByText('Industrial Warehouse Development')).toBeInTheDocument()
    expect(screen.getByText('Hosur, Tamil Nadu')).toBeInTheDocument()
    expect(screen.getAllByText('Active')).toHaveLength(2)
    expect(screen.getByText('Planning')).toBeInTheDocument()
    expect(screen.queryByText('COMING SOON')).not.toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: /My Profile/i }))
    expect(await screen.findByText('Account details')).toBeInTheDocument()
  })

  it('opens the project form and validates required fields', async () => {
    const user = userEvent.setup()
    window.location.hash = 'projects'
    render(<App />)
    await user.click(screen.getByRole('button', { name: '+ Add Project' }))
    expect(screen.getByRole('dialog', { name: 'Add project' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Save Project' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Project name, site address, city, and state are required.')
  })

  it('shows authenticated profile information and can sign out', async () => {
    request.mockImplementation((path) => {
      if (path === '/health/ready') return Promise.resolve({ status: 'ready' })
      if (path === '/api/auth/me') return Promise.resolve({ id: '1', email: 'worker@example.com', full_name: 'Site Worker' })
      return Promise.resolve({ items: [], total: 0 })
    })
    render(<App />)
    expect(await screen.findByText('Site Worker')).toBeInTheDocument()
    expect(screen.getByText('System connected')).toBeInTheDocument()
  })
})
