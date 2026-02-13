import './App.css'
import { useState, useCallback } from 'react'
import { ThemeProvider } from '@/components/theme-provider'
import { TourProvider } from '@/components/tour'
import { Layout } from '@/components/Layout'
import { EscalaPage } from '@/pages/EscalaPage'
import { ColaboradoresPage } from '@/pages/ColaboradoresPage'
import { PedidosPage } from '@/pages/PedidosPage'
import { ConfiguracaoPage } from '@/pages/ConfiguracaoPage'
import { PerfilPage } from '@/pages/PerfilPage'
import { Toaster } from '@/components/ui/sonner'
import type { Page } from '@/types'
import { TOUR_NAVIGATE_EVENT } from '@/lib/tour-constants'
import { useEffect } from 'react'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('escala')

  const onNavigate = useCallback((page: Page) => {
    setCurrentPage(page)
  }, [])

  useEffect(() => {
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent<Page>
      const nextPage = customEvent.detail
      if (
        nextPage === 'escala' ||
        nextPage === 'colaboradores' ||
        nextPage === 'pedidos' ||
        nextPage === 'configuracao' ||
        nextPage === 'perfil'
      ) {
        setCurrentPage(nextPage)
      }
    }
    window.addEventListener(TOUR_NAVIGATE_EVENT, handler)
    return () => window.removeEventListener(TOUR_NAVIGATE_EVENT, handler)
  }, [])

  return (
    <ThemeProvider defaultTheme="system" storageKey="escalaflow-theme">
      <TourProvider
        onComplete={() => localStorage.setItem('tourCompleted', 'true')}
        isTourCompleted={typeof window !== 'undefined' && localStorage.getItem('tourCompleted') === 'true'}
      >
        <Layout currentPage={currentPage} onNavigate={onNavigate}>
          {currentPage === 'escala' && <EscalaPage />}
          {currentPage === 'colaboradores' && <ColaboradoresPage />}
          {currentPage === 'pedidos' && <PedidosPage />}
          {currentPage === 'configuracao' && <ConfiguracaoPage />}
          {currentPage === 'perfil' && <PerfilPage />}
        </Layout>
        <Toaster />
      </TourProvider>
    </ThemeProvider>
  )
}

export default App
