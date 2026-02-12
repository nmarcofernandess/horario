"use client"

import * as React from "react"
import {
  Calendar,
  Users,
  FileText,
  Settings,
  Store,
  User,
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
      return { name: p.nome || "Usuário", avatar: p.fotoBase64 || "" }
    }
  } catch {}
  return { name: "Usuário", avatar: "" }
}

const pageToNav = (currentPage: Page) => ({
  user: {
    ...loadUserFromPerfil(),
    email: "Perfil local",
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
    {
      title: "Perfil",
      url: "perfil",
      icon: User,
      isActive: currentPage === "perfil",
      items: [],
    },
  ],
})

type Props = {
  currentPage: Page
  onNavigate: (page: Page) => void
}

export function AppSidebar({ currentPage, onNavigate }: Props) {
  const data = React.useMemo(() => pageToNav(currentPage), [currentPage])

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div id={TOUR_STEP_IDS.TEAM_SWITCHER} className="flex items-center gap-2 px-2 py-1">
          <div className="bg-sidebar-primary text-sidebar-primary-foreground flex size-8 items-center justify-center rounded-lg">
            <Store className="size-4" />
          </div>
          <div className="grid text-left text-sm leading-tight">
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
