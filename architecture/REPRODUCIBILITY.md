# Archify 재생성과 검증

| 대상 | 도면 원본 | 읽기 페이지 원본 | 기존 공개 주소 |
|---|---|---|---|
| 1차 논리 | `phase1-logical.architecture.json` | `phase1-logical.archify.md` | `../phase1_logical_current.html` |
| 1차 물리 | `phase1-physical.architecture.json` | `phase1-physical.archify.md` | `../phase1_physical_current.html` |
| 2차 논리 | `phase2-logical.architecture.json` | `phase2-logical.archify.md` | `../phase2_logical_architecture.html` |
| 2차 물리 | `phase2-physical.architecture.json` | `phase2-physical.archify.md` | `../phase2_physical_architecture.html` |

`catalog.json`은 이전 가이드 ID·설명 전문과 변환 기준을 보관합니다. 2차 논리의 안내 ID는 `primary-path`, `db-path`, `ipsec-vpn`, `netpol`, `cicd-image`, `platform`입니다. Archify 3.x에서 제거된 구형 Story/Guided View UI를 공식 단계별 설명으로 이전했습니다. 단계 선택과 노드 열람을 제공하지만, 과거 다중 노드 하이라이트·스토리 애니메이션과 동일하다고 표현하지 않습니다.

필요 환경은 Node.js 18 이상, Git, Chrome/Chromium 또는 Edge입니다. Archify는 별도 API 키 없이 로컬에서 생성·검증합니다. 도구 버전과 원본 커밋은 `toolchain.json`에 고정합니다. 개인 협업 지침이나 외부 AI 설정은 이 저장소의 정책에 포함하지 않습니다.

## 실행

저장소 루트에서 공식 도구를 한 번 준비합니다. 기존 경로가 있으면 덮어쓰지 말고 별도의 깨끗한 체크아웃을 `ARCHIFY_ROOT`로 지정합니다.

```powershell
git clone https://github.com/tt-a1i/archify.git .cache/archify
git -C .cache/archify checkout 25cf37080fc8b1dbe758a4efc3935b55f3327083
node scripts/build-architecture.mjs
node --test scripts/architecture.test.mjs
node scripts/build-architecture.mjs --check
```

별도 도구 위치를 쓰는 PowerShell 예:

```powershell
$env:ARCHIFY_ROOT = 'C:/path/to/clean-archify-checkout'
node scripts/build-architecture.mjs
```

빌드는 도구 커밋·버전·깨끗한 작업 상태와 입력의 출처 커밋을 확인합니다. 출처 공개 커밋을 Git에서 읽을 수 있어야 하므로 얕은 체크아웃은 해당 커밋을 추가 fetch해야 합니다. CI는 전체 이력을 가져옵니다.

## 정상 판정과 한계

- 도면 4개: `finalize architecture`의 정적·납품·실제 브라우저 검사 통과.
- 읽기 페이지 4개: `finalize explainer`의 정적·납품 검사 통과. 해당 명령은 브라우저 검사를 실행하지 않으므로 화면·단계 선택·대화형 보기·테마·내보내기는 별도 확인.
- 원본과 생성물의 일치, 2차 노드·관계 보존, 6개 안내 전문 보존, DB 접근과 노드 pull 통제 구분, 이전 1차 도면 미변경을 자동 시험.
- `build-manifest.json`에는 입력·출력 해시와 실제 게이트 결과만 기록. 로컬 절대 경로가 들어가는 상세 영수증은 무시된 sidecar와 `.archify-receipts/`에 두며 공개 커밋에 넣지 않음.
- 도면 자동 검사·화면 확인은 실제 서버 Runtime 검증이나 클라우드 통합·최종 인수가 아님.

## 실패와 복구

실패한 빌드나 일부 파일 통과를 전체 완료로 표시하지 않습니다. 실패하면 게시를 중단하고 해당 원본을 수정해 재생성합니다. 도구의 마지막 정상 출력 보존과 별개로, 여러 파일의 통합 상태를 확인한 뒤 커밋합니다. 작업 중인 다른 변경을 임의로 되돌리지 않습니다.

병합 후 문제가 생기면 해당 PR의 변경을 되돌려 이전 공개본으로 복구합니다. 서버 설정·시험·인수 기록은 도면 복구와 별개입니다. 내부 주소에 대한 추가 조사나 서버 변경을 이 생성 절차에 포함하지 않습니다.
