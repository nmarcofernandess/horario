import { describe, expect, it } from 'vitest'

import { formatRule, formatStatus } from './format'

describe('format helpers', () => {
  it('traduz status técnicos para termos de usuário', () => {
    expect(formatStatus('WORK')).toBe('Trabalho')
    expect(formatStatus('FOLGA')).toBe('Folga')
    expect(formatStatus('ABSENCE')).toBe('Ausência')
  })

  it('harmoniza labels de regras atuais e legadas', () => {
    expect(formatRule('R4_WEEKLY_TARGET')).toBe('Meta semanal de horas')
    expect(formatRule('R5_DEMAND_COVERAGE')).toBe('Cobertura insuficiente')
    expect(formatRule('R4_DEMAND_COVERAGE')).toBe('Cobertura insuficiente')
    expect(formatRule('R6_MAX_DAILY_MINUTES')).toBe('Limite diário de jornada')
  })
})
