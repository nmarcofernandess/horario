import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { EscalaPage } from './EscalaPage'

const mocks = vi.hoisted(() => ({
  generateMock: vi.fn(),
  simulateMock: vi.fn(),
  getAssignmentsMock: vi.fn(),
  getViolationsMock: vi.fn(),
  weeklyAnalysisMock: vi.fn(),
  preflightMock: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
  api: {
    scale: {
      generate: mocks.generateMock,
      simulate: mocks.simulateMock,
      getAssignments: mocks.getAssignmentsMock,
      getViolations: mocks.getViolationsMock,
      weeklyAnalysis: mocks.weeklyAnalysisMock,
      preflight: mocks.preflightMock,
    },
    export: {
      html: () => 'http://example/html',
      markdown: () => 'http://example/md',
    },
  },
}))

describe('EscalaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getAssignmentsMock.mockResolvedValue([
      {
        work_date: '2026-02-10',
        employee_id: 'OFICIAL_ID',
        employee_name: 'Colaborador Oficial',
        status: 'WORK',
        shift_code: 'CAI1',
        minutes: 480,
      },
    ])
    mocks.getViolationsMock.mockResolvedValue([])
    mocks.generateMock.mockResolvedValue({ status: 'SUCCESS', assignments_count: 1, violations_count: 0 })
    mocks.weeklyAnalysisMock.mockResolvedValue({
      period_start: '2026-02-08',
      period_end: '2026-03-31',
      sector_id: 'CAIXA',
      policy_week_definition: 'MON_SUN',
      tolerance_minutes: 30,
      summaries_mon_sun: [],
      summaries_sun_sat: [],
      external_dependencies_open: [],
    })
    mocks.preflightMock.mockResolvedValue({
      mode: 'NORMAL',
      blockers: [],
      critical_warnings: [],
      can_proceed: true,
      ack_required: false,
    })
    mocks.simulateMock.mockResolvedValue({
      status: 'SUCCESS',
      assignments_count: 1,
      violations_count: 1,
      preferences_processed: 0,
      exceptions_applied: 0,
      assignments: [
        {
          work_date: '2026-02-11',
          employee_id: 'SIM_ID',
          employee_name: 'Colaborador Simulado',
          status: 'FOLGA',
          shift_code: '',
          minutes: 0,
        },
      ],
      violations: [
        {
          employee_id: 'SIM_ID',
          employee_name: 'Colaborador Simulado',
          rule_code: 'R5_DEMAND_COVERAGE',
          rule_label: 'Cobertura insuficiente',
          severity: 'MEDIUM',
          detail: 'Teste de simulação',
        },
      ],
    })
  })

  it('alterna entre escala oficial e simulação', async () => {
    const user = userEvent.setup()
    render(<EscalaPage />)

    await screen.findByText('Colaborador Oficial')

    await user.click(screen.getByRole('button', { name: 'Simular período' }))

    await waitFor(() => {
      expect(screen.getByText('Visualizando uma simulação. Nenhum dado oficial foi sobrescrito.')).toBeInTheDocument()
    })

    expect(screen.getByText('Colaborador Simulado')).toBeInTheDocument()
    expect(screen.getByText('Cobertura insuficiente')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Ver escala oficial' }))

    expect(screen.queryByText('Visualizando uma simulação. Nenhum dado oficial foi sobrescrito.')).not.toBeInTheDocument()
    expect(screen.getByText('Colaborador Oficial')).toBeInTheDocument()
    expect(mocks.simulateMock).toHaveBeenCalledTimes(1)
  })

  it('exige justificativa quando preflight pede ack em modo estrito', async () => {
    const user = userEvent.setup()
    mocks.preflightMock.mockResolvedValueOnce({
      mode: 'ESTRITO',
      blockers: [],
      critical_warnings: [
        {
          code: 'LEGAL_SOFT_1',
          message: 'Pendência jurídica de domingo/feriado.',
          recommended_action: 'Registrar justificativa operacional.',
        },
      ],
      can_proceed: true,
      ack_required: true,
    })
    mocks.generateMock.mockResolvedValueOnce({ status: 'SUCCESS', assignments_count: 1, violations_count: 0 })

    render(<EscalaPage />)
    await screen.findByText('Colaborador Oficial')
    await user.click(screen.getByRole('button', { name: 'Gerar escala' }))

    expect(screen.getByText('Continuar com risco legal')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Motivo obrigatório'), 'Fechamento emergencial do período.')
    await user.click(screen.getByRole('button', { name: 'Continuar e registrar justificativa' }))

    await waitFor(() => expect(mocks.generateMock).toHaveBeenCalled())
  })

  it('bloqueia visualmente quando há LOGIC_HARD no preflight', async () => {
    const user = userEvent.setup()
    mocks.preflightMock.mockResolvedValueOnce({
      mode: 'NORMAL',
      blockers: [
        {
          code: 'LOGIC_EMPTY_TEMPLATE',
          message: 'Mosaico semanal vazio para o setor.',
          recommended_action: 'Preencha o mosaico semanal.',
        },
      ],
      critical_warnings: [],
      can_proceed: false,
      ack_required: false,
    })
    render(<EscalaPage />)
    await screen.findByText('Colaborador Oficial')
    await user.click(screen.getByRole('button', { name: 'Gerar escala' }))
    expect(screen.getByText('Impossível lógico (bloqueado)')).toBeInTheDocument()
    expect(mocks.generateMock).not.toHaveBeenCalled()
  })
})
