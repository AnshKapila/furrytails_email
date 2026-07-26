export async function GET() {
  return Response.json({ app: 'ok', at: Date.now() });
}
