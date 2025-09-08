import { describe, it, expect, vi } from "vitest";
import { parseEventStream } from "../lib/sse";

function streamFromString(s: string): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  const chunks = s.split("")
  return new ReadableStream({
    start(controller) {
      controller.enqueue(enc.encode(s));
      controller.close();
    }
  });
}

describe("SSE parser", () => {
  it("parses context, token(s), done with CRLF", async () => {
    const data = [
      "event: context\r\ndata: {\"a\":1}\r\n\r\n",
      "event: token\r\ndata: {\"t\":\"Hi \"}\r\n\r\n",
      "event: token\r\ndata: {\"t\":\"there\"}\r\n\r\n",
      "event: done\r\ndata: {\"finish_reason\":\"stop\"}\r\n\r\n",
    ].join("");
    const events: Array<[string,string]> = [];
    await parseEventStream(streamFromString(data), (e, d) => events.push([e,d]), () => {}, () => {});
    expect(events.map(e => e[0])).toEqual(["context","token","token","done"]);
  });
});

