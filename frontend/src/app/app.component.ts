import { Component, inject } from "@angular/core";
import { RouterOutlet } from "@angular/router";

import { ThemeService } from "./core/theme.service";

@Component({
  selector: "kh-root",
  imports: [RouterOutlet],
  template: "<router-outlet />",
})
export class AppComponent {
  // Cria o serviço no bootstrap para aplicar o tema também na tela de login.
  readonly theme = inject(ThemeService);
}
