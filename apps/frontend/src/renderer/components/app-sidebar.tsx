"use client"

import * as React from "react"
import { PERFIL_UPDATED_EVENT } from "@/lib/perfil"
import {
  Calendar,
  Users,
  FileText,
  Settings,
  Store,
} from "lucide-react"
import type { Page } from "@/types"
import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { TOUR_STEP_IDS } from "@/lib/tour-constants"

function loadUserFromPerfil() {
  try {
    const s = localStorage.getItem("escalaflow-perfil")
    if (s) {
      const p = JSON.parse(s)
      return {
        name: p.nome || "Usuário",
        avatar: p.fotoBase64 || "",
        organizacao: p.organizacao || "",
      }
    }
  } catch { /* ignore parse errors */ }
  return { name: "Usuário", avatar: "", organizacao: "" }
}

const pageToNav = (currentPage: Page) => {
  const perfil = loadUserFromPerfil()
  return {
  user: {
    name: perfil.name,
    avatar: perfil.avatar,
    email: perfil.organizacao || "Perfil local",
  },
  navMain: [
    {
      title: "Escala de Trabalho",
      url: "escala",
      icon: Calendar,
      isActive: currentPage === "escala",
      items: [],
    },
    {
      title: "Colaboradores",
      url: "colaboradores",
      icon: Users,
      isActive: currentPage === "colaboradores",
      items: [],
    },
    {
      title: "Pedidos",
      url: "pedidos",
      icon: FileText,
      isActive: currentPage === "pedidos",
      items: [],
    },
    {
      title: "Configuração",
      url: "configuracao",
      icon: Settings,
      isActive: currentPage === "configuracao",
      items: [],
    },
  ],
}
}

type Props = {
  currentPage: Page
  onNavigate: (page: Page) => void
}

export function AppSidebar({ currentPage, onNavigate }: Props) {
  const [perfilVersion, setPerfilVersion] = React.useState(0)
  React.useEffect(() => {
    const handler = () => setPerfilVersion((v) => v + 1)
    window.addEventListener(PERFIL_UPDATED_EVENT, handler)
    return () => window.removeEventListener(PERFIL_UPDATED_EVENT, handler)
  }, [])
  const data = React.useMemo(() => pageToNav(currentPage), [currentPage, perfilVersion])

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div id={TOUR_STEP_IDS.TEAM_SWITCHER} className="flex items-center gap-2 px-2 py-1 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0">
          <div className="bg-sidebar-primary text-sidebar-primary-foreground flex size-8 shrink-0 items-center justify-center rounded-lg">
            <Store className="size-4" />
          </div>
          <div className="grid min-w-0 flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
            <span className="truncate font-medium">EscalaFlow</span>
            <span className="truncate text-xs text-muted-foreground">Operação local</span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <div id={TOUR_STEP_IDS.NAV_MAIN}>
          <NavMain items={data.navMain} onNavigate={(url) => onNavigate(url as Page)} />
        </div>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} onNavigate={(url) => onNavigate(url as Page)} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
