import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function ConfiguracaoPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Configuração</h1>
      <Tabs defaultValue="turnos">
        <TabsList>
          <TabsTrigger value="turnos">Turnos</TabsTrigger>
          <TabsTrigger value="mosaico">Mosaico</TabsTrigger>
          <TabsTrigger value="rodizio">Rodízio</TabsTrigger>
          <TabsTrigger value="excecoes">Férias e ausências</TabsTrigger>
          <TabsTrigger value="demand">Demanda por horário</TabsTrigger>
        </TabsList>
        <TabsContent value="turnos">
          <Card>
            <CardHeader>
              <CardTitle>Turnos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Horários de cada turno (manhã, tarde, domingo).</p>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="mosaico">
          <Card>
            <CardHeader>
              <CardTitle>Mosaico</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Modelo padrão de turnos por dia da semana.</p>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="rodizio">
          <Card>
            <CardHeader>
              <CardTitle>Rodízio de domingos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Ordem de quem trabalha aos domingos e como compensa folga.</p>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="excecoes">
          <Card>
            <CardHeader>
              <CardTitle>Férias e ausências</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Datas em que o colaborador não pode trabalhar — férias, atestados, trocas.</p>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="demand">
          <Card>
            <CardHeader>
              <CardTitle>Demanda por horário</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Quantidade de pessoas necessárias em cada período do dia.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
