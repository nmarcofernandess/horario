"use client"

import * as React from "react"
import {
  Calendar,
  Users,
  FileText,
  Settings,
  LayoutDashboard,
  Store,
} from "lucide-react"
import type { Page } from "@/types"
import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { TOUR_STEP_IDS } from "@/lib/tour-constants"

const pageToNav = (currentPage: Page) => ({
  user: {
    name: "Supermercado Fernandes",
    email: "contato@supermercadofernandes.com.br",
    avatar: "",
  },
  teams: [
    {
      name: "Supermercado Fernandes",
      logo: Store,
      plan: "EscalaFlow",
    },
  ],
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
  projects: [
    {
      name: "Caixa",
      url: "#",
      icon: LayoutDashboard,
    },
    {
      name: "PDV",
      url: "#",
      icon: FileText,
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
        <div id={TOUR_STEP_IDS.TEAM_SWITCHER}>
          <TeamSwitcher teams={data.teams} />
        </div>
      </SidebarHeader>
      <SidebarContent>
        <div id={TOUR_STEP_IDS.NAV_MAIN}>
          <NavMain items={data.navMain} onNavigate={(url) => onNavigate(url as Page)} />
          <NavProjects projects={data.projects} />
        </div>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
