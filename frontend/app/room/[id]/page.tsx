import Desk from "./desk";

export default async function RoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <Desk roomId={id} />;
}
