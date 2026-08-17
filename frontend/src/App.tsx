import { useEffect, useMemo, useState } from 'react'

import {
  API_BASE_URL,
  checkApiHealth,
  checkDbHealth,
  createParcel,
  deleteParcel,
  getParcel,
  getParcelNeighbors,
  searchParcels,
  updateParcel,
  type GeoJSONPolygon,
  type Parcel,
} from './api'

const sampleGeometry = JSON.stringify(
  {
    type: 'Polygon',
    coordinates: [[[1.45, 43.61], [1.46, 43.61], [1.46, 43.62], [1.45, 43.61]]],
  },
  null,
  2,
)

function parseGeometry(value: string): GeoJSONPolygon {
  return JSON.parse(value) as GeoJSONPolygon
}

function formatSurface(value: string | number): string {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) {
    return String(value)
  }
  return `${parsed.toFixed(2)} m2`
}

function extractPolygons(parcels: Parcel[]): number[][][] {
  return parcels
    .map((parcel) => parcel.geometry.coordinates[0])
    .filter((ring) => Array.isArray(ring) && ring.length >= 3)
}

function GeometryPreview({ parcels }: { parcels: Parcel[] }) {
  const rings = useMemo(() => extractPolygons(parcels), [parcels])

  if (rings.length === 0) {
    return (
      <div className="empty-preview">
        Aucune geometrie a visualiser.
      </div>
    )
  }

  const allPoints = rings.flat()
  const longitudes = allPoints.map((point) => point[0])
  const latitudes = allPoints.map((point) => point[1])
  const minLon = Math.min(...longitudes)
  const maxLon = Math.max(...longitudes)
  const minLat = Math.min(...latitudes)
  const maxLat = Math.max(...latitudes)
  const lonSpan = Math.max(maxLon - minLon, 0.00001)
  const latSpan = Math.max(maxLat - minLat, 0.00001)

  const toX = (lon: number) => ((lon - minLon) / lonSpan) * 720 + 20
  const toY = (lat: number) => 360 - ((lat - minLat) / latSpan) * 320

  return (
    <svg viewBox="0 0 760 380" className="geometry-preview" role="img" aria-label="Visualisation des parcelles">
      <rect x="0" y="0" width="760" height="380" className="preview-background" />
      {rings.map((ring, index) => {
        const d = ring
          .map((point, pointIndex) => {
            const x = toX(point[0])
            const y = toY(point[1])
            return `${pointIndex === 0 ? 'M' : 'L'} ${x} ${y}`
          })
          .join(' ')
        return (
          <path
            key={`${index}-${d}`}
            d={`${d} Z`}
            className="preview-polygon"
            style={{
              animationDelay: `${index * 60}ms`,
            }}
          />
        )
      })}
    </svg>
  )
}

function App() {
  const [apiHealth, setApiHealth] = useState('Verification en cours...')
  const [dbHealth, setDbHealth] = useState('Verification en cours...')
  const [statusMessage, setStatusMessage] = useState('Pret.')

  const [createCodeInsee, setCreateCodeInsee] = useState('31555')
  const [createPrefixe, setCreatePrefixe] = useState('001')
  const [createSection, setCreateSection] = useState('AA')
  const [createNumero, setCreateNumero] = useState('123')
  const [createGeometry, setCreateGeometry] = useState(sampleGeometry)

  const [parcelIdInput, setParcelIdInput] = useState('1')
  const [currentParcel, setCurrentParcel] = useState<Parcel | null>(null)

  const [updateCodeInsee, setUpdateCodeInsee] = useState('')
  const [updatePrefixe, setUpdatePrefixe] = useState('')
  const [updateSection, setUpdateSection] = useState('')
  const [updateNumero, setUpdateNumero] = useState('')
  const [updateGeometry, setUpdateGeometry] = useState('')

  const [searchGeometry, setSearchGeometry] = useState(sampleGeometry)
  const [searchLimit, setSearchLimit] = useState('100')
  const [searchOffset, setSearchOffset] = useState('0')
  const [searchResults, setSearchResults] = useState<Parcel[]>([])

  const [neighborParcelId, setNeighborParcelId] = useState('1')
  const [neighborLimit, setNeighborLimit] = useState('100')
  const [neighborOffset, setNeighborOffset] = useState('0')
  const [neighborResults, setNeighborResults] = useState<Parcel[]>([])

  const [isBusy, setIsBusy] = useState(false)

  const visibleParcels = useMemo(() => {
    const byId = new Map<number, Parcel>()
    if (currentParcel) {
      byId.set(currentParcel.id, currentParcel)
    }
    for (const item of searchResults) {
      byId.set(item.id, item)
    }
    for (const item of neighborResults) {
      byId.set(item.id, item)
    }
    return Array.from(byId.values())
  }, [currentParcel, searchResults, neighborResults])

  useEffect(() => {
    async function loadHealth(): Promise<void> {
      try {
        const [apiMessage, dbMessage] = await Promise.all([
          checkApiHealth(),
          checkDbHealth(),
        ])
        setApiHealth(apiMessage)
        setDbHealth(dbMessage)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Erreur inconnue.'
        setApiHealth(message)
        setDbHealth(message)
      }
    }

    void loadHealth()
  }, [])

  async function runAction(action: () => Promise<void>): Promise<void> {
    setIsBusy(true)
    try {
      await action()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erreur inconnue.'
      setStatusMessage(message)
    } finally {
      setIsBusy(false)
    }
  }

  async function handleCreate(): Promise<void> {
    await runAction(async () => {
      const created = await createParcel({
        code_insee: createCodeInsee.trim(),
        prefixe: createPrefixe.trim(),
        section: createSection.trim(),
        numero: createNumero.trim(),
        geometry: parseGeometry(createGeometry),
      })
      setCurrentParcel(created)
      setParcelIdInput(String(created.id))
      setStatusMessage(`Parcelle ${created.id} creee avec succes.`)
    })
  }

  async function handleGetById(): Promise<void> {
    await runAction(async () => {
      const found = await getParcel(Number(parcelIdInput))
      setCurrentParcel(found)
      setStatusMessage(`Parcelle ${found.id} chargee.`)
    })
  }

  async function handleUpdate(): Promise<void> {
    await runAction(async () => {
      const payload: Record<string, unknown> = {}
      if (updateCodeInsee.trim()) payload.code_insee = updateCodeInsee.trim()
      if (updatePrefixe.trim()) payload.prefixe = updatePrefixe.trim()
      if (updateSection.trim()) payload.section = updateSection.trim()
      if (updateNumero.trim()) payload.numero = updateNumero.trim()
      if (updateGeometry.trim()) payload.geometry = parseGeometry(updateGeometry)

      const updated = await updateParcel(Number(parcelIdInput), payload)
      setCurrentParcel(updated)
      setStatusMessage(`Parcelle ${updated.id} mise a jour.`)
    })
  }

  async function handleDelete(): Promise<void> {
    await runAction(async () => {
      await deleteParcel(Number(parcelIdInput))
      setCurrentParcel(null)
      setStatusMessage(`Parcelle ${parcelIdInput} supprimee.`)
    })
  }

  async function handleSearch(): Promise<void> {
    await runAction(async () => {
      const results = await searchParcels({
        geometry: parseGeometry(searchGeometry),
        limit: Number(searchLimit),
        offset: Number(searchOffset),
      })
      setSearchResults(results)
      setStatusMessage(`Recherche terminee: ${results.length} resultat(s).`)
    })
  }

  async function handleNeighbors(): Promise<void> {
    await runAction(async () => {
      const results = await getParcelNeighbors(
        Number(neighborParcelId),
        Number(neighborLimit),
        Number(neighborOffset),
      )
      setNeighborResults(results)
      setStatusMessage(`Voisinage charge: ${results.length} voisin(s).`)
    })
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">GeoFoncier</p>
          <h1>Console parcellaire</h1>
          <p className="lead">
            Interface de demonstration complete pour le jury: CRUD, recherche
            spatiale, voisins et verification de sante API.
          </p>
          <p className="api-url">Base API: {API_BASE_URL}</p>
        </div>
        <div className="health-cards">
          <article>
            <h2>Etat API</h2>
            <p>{apiHealth}</p>
          </article>
          <article>
            <h2>Etat Base</h2>
            <p>{dbHealth}</p>
          </article>
        </div>
      </header>

      <section className="workspace">
        <div className="pane pane-left">
          <section className="card">
            <h3>Creation</h3>
            <div className="grid two-cols">
              <label>
                Code INSEE
                <input value={createCodeInsee} onChange={(event) => setCreateCodeInsee(event.target.value)} />
              </label>
              <label>
                Prefixe
                <input value={createPrefixe} onChange={(event) => setCreatePrefixe(event.target.value)} />
              </label>
              <label>
                Section
                <input value={createSection} onChange={(event) => setCreateSection(event.target.value)} />
              </label>
              <label>
                Numero
                <input value={createNumero} onChange={(event) => setCreateNumero(event.target.value)} />
              </label>
            </div>
            <label>
              Geometry GeoJSON
              <textarea value={createGeometry} onChange={(event) => setCreateGeometry(event.target.value)} rows={7} />
            </label>
            <button disabled={isBusy} onClick={() => void handleCreate()}>
              Creer la parcelle
            </button>
          </section>

          <section className="card">
            <h3>Lecture / Mise a jour / Suppression</h3>
            <label>
              ID parcelle
              <input value={parcelIdInput} onChange={(event) => setParcelIdInput(event.target.value)} />
            </label>
            <div className="button-row">
              <button disabled={isBusy} onClick={() => void handleGetById()}>
                Charger
              </button>
              <button className="danger" disabled={isBusy} onClick={() => void handleDelete()}>
                Supprimer
              </button>
            </div>

            <div className="grid two-cols">
              <label>
                Code INSEE (optionnel)
                <input value={updateCodeInsee} onChange={(event) => setUpdateCodeInsee(event.target.value)} />
              </label>
              <label>
                Prefixe (optionnel)
                <input value={updatePrefixe} onChange={(event) => setUpdatePrefixe(event.target.value)} />
              </label>
              <label>
                Section (optionnel)
                <input value={updateSection} onChange={(event) => setUpdateSection(event.target.value)} />
              </label>
              <label>
                Numero (optionnel)
                <input value={updateNumero} onChange={(event) => setUpdateNumero(event.target.value)} />
              </label>
            </div>

            <label>
              Geometry GeoJSON (optionnelle)
              <textarea value={updateGeometry} onChange={(event) => setUpdateGeometry(event.target.value)} rows={5} placeholder="Laisser vide pour ne pas changer la geometrie." />
            </label>
            <button disabled={isBusy} onClick={() => void handleUpdate()}>
              Mettre a jour
            </button>
          </section>

          <section className="card">
            <h3>Recherche spatiale</h3>
            <label>
              Geometry GeoJSON
              <textarea value={searchGeometry} onChange={(event) => setSearchGeometry(event.target.value)} rows={6} />
            </label>
            <div className="grid two-cols">
              <label>
                Limit
                <input value={searchLimit} onChange={(event) => setSearchLimit(event.target.value)} />
              </label>
              <label>
                Offset
                <input value={searchOffset} onChange={(event) => setSearchOffset(event.target.value)} />
              </label>
            </div>
            <button disabled={isBusy} onClick={() => void handleSearch()}>
              Lancer la recherche
            </button>
          </section>

          <section className="card">
            <h3>Voisins</h3>
            <div className="grid three-cols">
              <label>
                Parcel ID
                <input value={neighborParcelId} onChange={(event) => setNeighborParcelId(event.target.value)} />
              </label>
              <label>
                Limit
                <input value={neighborLimit} onChange={(event) => setNeighborLimit(event.target.value)} />
              </label>
              <label>
                Offset
                <input value={neighborOffset} onChange={(event) => setNeighborOffset(event.target.value)} />
              </label>
            </div>
            <button disabled={isBusy} onClick={() => void handleNeighbors()}>
              Charger les voisins
            </button>
          </section>
        </div>

        <aside className="pane pane-right">
          <section className="card status-card">
            <h3>Journal</h3>
            <p>{statusMessage}</p>
          </section>

          <section className="card">
            <h3>Visualisation</h3>
            <GeometryPreview parcels={visibleParcels} />
          </section>

          <section className="card">
            <h3>Parcelle courante</h3>
            {currentParcel ? (
              <ul className="result-list">
                <li>ID: {currentParcel.id}</li>
                <li>Reference: {currentParcel.code_insee}-{currentParcel.prefixe}-{currentParcel.section}-{currentParcel.numero}</li>
                <li>Surface: {formatSurface(currentParcel.surface_m2)}</li>
              </ul>
            ) : (
              <p>Aucune parcelle selectionnee.</p>
            )}
          </section>

          <section className="card">
            <h3>Resultats recherche ({searchResults.length})</h3>
            <ul className="result-list">
              {searchResults.map((item) => (
                <li key={`search-${item.id}`}>
                  #{item.id} - {item.code_insee}/{item.section}/{item.numero}
                </li>
              ))}
            </ul>
          </section>

          <section className="card">
            <h3>Voisins ({neighborResults.length})</h3>
            <ul className="result-list">
              {neighborResults.map((item) => (
                <li key={`neighbor-${item.id}`}>
                  #{item.id} - {item.code_insee}/{item.section}/{item.numero}
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </section>
    </main>
  )
}

export default App
