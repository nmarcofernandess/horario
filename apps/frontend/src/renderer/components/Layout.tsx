import type { Page } from '@/types'
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { TourSetup } from '@/components/tour-setup'
import { ApiStatus } from '@/components/ApiStatus'
import { TOUR_STEP_IDS } from '@/lib/tour-constants'

type Props = {
  currentPage: Page
  onNavigate: (page: Page) => void
  children: React.ReactNode
}

export function Layout({ currentPage, onNavigate, children }: Props) {
  return (
    <SidebarProvider>
      <TourSetup />
      <AppSidebar currentPage={currentPage} onNavigate={onNavigate} />
      <main className="flex min-h-svh flex-1 flex-col overflow-auto bg-background">
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background px-6">
          <SidebarTrigger
            className="-ml-2 size-9 shrink-0"
            aria-label="Alternar menu (⌘B / Ctrl+B)"
          />
          <div className="flex-1">
            <h1 className="text-base font-semibold tracking-tight text-foreground">EscalaFlow</h1>
          </div>
          <ApiStatus />
        </header>
        <div id={TOUR_STEP_IDS.CONTENT_AREA} className="flex-1 p-6">
          <div className="mx-auto w-full max-w-6xl">
            {children}
          </div>
        </div>
      </main>
    </SidebarProvider>
  )
}
