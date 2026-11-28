import { Replay } from "./replay";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  return <Replay roomId={(await params).id} />;
}
