import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NoticeService } from '../core/notice.service';
import { BillsPageComponent } from './bills.component';
import { BrandsPageComponent } from './brands.component';
import { DashboardPageComponent } from './dashboard.component';
import { FarmersPageComponent } from './farmers.component';
import { KhataPageComponent } from './khata.component';
import { PosPageComponent } from './pos.component';
import { ProductsPageComponent } from './products.component';
import { SeasonsPageComponent } from './seasons.component';
import { SettingsPageComponent } from './settings.component';
import { StockPageComponent } from './stock.component';

@Component({
  selector: 'app-feature',
  standalone: true,
  imports: [
    CommonModule,
    DashboardPageComponent,
    PosPageComponent,
    BrandsPageComponent,
    ProductsPageComponent,
    StockPageComponent,
    FarmersPageComponent,
    SeasonsPageComponent,
    BillsPageComponent,
    KhataPageComponent,
    SettingsPageComponent,
  ],
  templateUrl: './app-feature.component.html',
  styleUrls: ['./app-feature.component.scss'],
})
export class AppFeatureComponent {
  private readonly route = inject(ActivatedRoute);
  readonly notice = inject(NoticeService);
  readonly page = String(this.route.snapshot.data['page'] ?? 'dashboard');
}
