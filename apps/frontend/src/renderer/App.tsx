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

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('escala')

  const onNavigate = useCallback((page: Page) => {
    setCurrentPage(page)
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
