import { ComponentFixture, TestBed } from '@angular/core/testing';

// import { Alerts } from './alerts';
import { AlertsComponent } from './alerts';
describe('Alerts', () => {
  let component: AlertsComponent;
  let fixture: ComponentFixture<AlertsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlertsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AlertsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
