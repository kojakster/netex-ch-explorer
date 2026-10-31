import { fireEvent, render, screen } from "@testing-library/react";
import { OpenFiles } from "./OpenFiles";

describe("OpenFiles", () => {
  it("bietet den Dialog „Datei öffnen“ für mehrere XML- oder eine ZIP-Datei an", () => {
    render(<OpenFiles onOpen={() => undefined} />);
    const input = screen.getByLabelText("Dateien auswählen") as HTMLInputElement;
    expect(input.type).toBe("file");
    expect(input.multiple).toBe(true);
    expect(input.accept).toContain(".xml");
    expect(input.accept).toContain(".zip");
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("öffnet den Dateidialog über den Knopf", () => {
    render(<OpenFiles onOpen={() => undefined} />);
    const input = screen.getByLabelText("Dateien auswählen") as HTMLInputElement;
    const click = vi.spyOn(input, "click");
    fireEvent.click(screen.getByRole("button", { name: "Datei öffnen …" }));
    expect(click).toHaveBeenCalled();
  });

  it("meldet die gewählten Dateien", () => {
    const onOpen = vi.fn();
    render(<OpenFiles onOpen={onOpen} />);
    const files = [new File(["<a/>"], "a.xml"), new File(["<b/>"], "b.xml")];
    fireEvent.change(screen.getByLabelText("Dateien auswählen"), { target: { files } });
    expect(onOpen).toHaveBeenCalledWith(files);
  });

  it("ignoriert eine leere Auswahl", () => {
    const onOpen = vi.fn();
    render(<OpenFiles onOpen={onOpen} />);
    fireEvent.change(screen.getByLabelText("Dateien auswählen"), { target: { files: [] } });
    expect(onOpen).not.toHaveBeenCalled();
  });
});
